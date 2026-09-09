"""Manifest-first PTB-XL baselines and ECG MODEL_V1 runner.

This Phase 3 entry point never creates its own split and never fits
preprocessing on validation or test data. Synthetic data is not accepted.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datasets.ptbxl import PTBXLDataset, PTBXLRecord
from evaluation.metrics import compute_metrics
from features.ecg_features import ECGFeatureExtractor
from preprocessing.ecg import ECGPreprocessor
from preprocessing.quality_ecg import ECGQualityAssessor
from preprocessing.windowing import ECGWindower

logger = logging.getLogger("ptbxl_baselines")


def _git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def load_locked_manifest(dataset, manifest_path, split_path, seed, max_records=None):
    """Load a split manifest or build it once from the record manifest."""
    import pandas as pd
    if split_path.exists():
        manifest = pd.read_csv(split_path)
        required = {"participant_id", "record_id", "label_int", "split"}
        missing = required - set(manifest.columns)
        if missing:
            raise ValueError(f"Split manifest missing columns: {sorted(missing)}")
    else:
        manifest = dataset.build_manifest(str(manifest_path), max_records=max_records)
        manifest = dataset.generate_splits(manifest, seed=seed, output_path=str(split_path))

    if max_records is not None and len(manifest) > max_records:
        manifest = manifest.sort_values("record_id").head(max_records).copy()
    if manifest["split"].isna().any() or not set(manifest["split"]).issubset({"train", "val", "test"}):
        raise ValueError("Manifest contains invalid or missing split assignments")
    for first, second in (("train", "val"), ("train", "test"), ("val", "test")):
        a = set(manifest.loc[manifest.split == first, "participant_id"])
        b = set(manifest.loc[manifest.split == second, "participant_id"])
        if a & b:
            raise ValueError("Participant overlap detected in PTB-XL split manifest")
    return manifest


def _record_map(dataset) -> Dict[str, PTBXLRecord]:
    return {r.record_id: r for r in dataset.load_all_records() if r.is_valid}


def materialize_windows(dataset, manifest, output_dir, max_train_fit_records=None):
    """Fit on train records, then transform every partition into fixed windows."""
    records = _record_map(dataset)
    train_rows = manifest[manifest.split == "train"]
    if max_train_fit_records is not None:
        train_rows = train_rows.sort_values("record_id").head(max_train_fit_records)
    fit_signals = []
    for row in train_rows.itertuples():
        record = records.get(row.record_id)
        if record is not None:
            fit_signals.append(dataset.load_signal(record)[0])
    if not fit_signals:
        raise RuntimeError("No valid PTB-XL training signals available for fitting")

    preprocessor = ECGPreprocessor().fit(fit_signals, source_fs=500)
    output_dir.mkdir(parents=True, exist_ok=True)
    preprocessor.save_normalization_stats(output_dir / "preprocessing.json")
    windower = ECGWindower(window_seconds=10, stride_seconds=5, sampling_rate=250)
    assessor = ECGQualityAssessor(fs=250)
    signals: Dict[str, List[np.ndarray]] = {"train": [], "val": [], "test": []}
    labels: Dict[str, List[int]] = {"train": [], "val": [], "test": []}

    for row in manifest.itertuples():
        record = records.get(row.record_id)
        if record is None:
            continue
        raw, fs = dataset.load_signal(record)
        processed = preprocessor.transform(raw, fs, row.record_id, "ptbxl")
        windows = windower.window_signal(
            processed.signal, row.participant_id, row.record_id,
            row.label_canonical, int(row.label_int), row.split, "ptbxl",
            getattr(row, "dataset_version", "1.0.1"),
        )
        for window in windows:
            quality = assessor.assess(window.signal)
            if quality.is_usable:
                signals[row.split].append(window.signal.astype(np.float32))
                labels[row.split].append(int(row.label_int))

    result = {s: (np.asarray(signals[s]), np.asarray(labels[s], dtype=np.int64)) for s in signals}
    with (output_dir / "data_summary.json").open("w") as handle:
        json.dump({s: {"n_windows": len(y), "normal": int(np.sum(y == 0)),
                       "abnormal": int(np.sum(y == 1))}
                   for s, (_, y) in result.items()}, handle, indent=2)
    return result, preprocessor


def _save_result(path, experiment, model, data, dataset, seed):
    path.mkdir(parents=True, exist_ok=True)
    train_x, train_y = data["train"]
    results = {}
    for split in ("val", "test"):
        x, y = data[split]
        if len(y) == 0:
            continue
        started = time.perf_counter()
        if experiment == "majority":
            pred = np.full(len(y), int(np.bincount(train_y).argmax()))
            prob = np.full(len(y), float(np.mean(train_y)))
        else:
            pred = model.predict(x)
            prob = model.predict_proba(x)[:, 1]
        latency = (time.perf_counter() - started) * 1000 / len(y)
        metric = compute_metrics(y, pred, prob, split=split, model_name=experiment, dataset=dataset)
        payload = metric.to_dict()
        payload["inference_latency_ms_per_window"] = round(latency, 4)
        results[split] = payload
    with (path / "results.json").open("w") as handle:
        json.dump({"experiment": experiment, "dataset": dataset, "seed": seed,
                   "git_commit": _git_revision(), "results": results}, handle, indent=2)
    return results


def run_classical(data, output_dir, dataset, seed):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    extractor = ECGFeatureExtractor(fs=250)
    features = {}
    for split, (signals, labels) in data.items():
        extracted = extractor.extract_batch(signals)
        nonfinite = int(np.sum(~np.isfinite(extracted)))
        if nonfinite:
            logger.warning("%s feature matrix contained %d non-finite values; replacing with 0", split, nonfinite)
            extracted = np.nan_to_num(extracted, nan=0.0, posinf=0.0, neginf=0.0)
        features[split] = (extracted, labels)
    train_x, train_y = features["train"]
    models = {
        "majority": None,
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed),
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=12, class_weight="balanced",
            random_state=seed, n_jobs=-1,
        ),
    }
    for name, model in models.items():
        (output_dir / name).mkdir(parents=True, exist_ok=True)
        if model is not None:
            model.fit(train_x, train_y)
            joblib.dump(model, output_dir / name / "model.pkl")
        result = _save_result(output_dir / name, name, model, features, dataset, seed)
        with (output_dir / name / "config.json").open("w") as handle:
            json.dump({"dataset": dataset, "seed": seed, "feature_version": "1.0.0",
                       "n_features": extractor.n_features, "git_commit": _git_revision()},
                      handle, indent=2)
        logger.info("%s complete: validation F1=%s", name, result.get("val", {}).get("f1"))


def run_cnn(data, output_dir, dataset, seed, epochs, batch_size, lr=0.001, patience=7, model_version="MODEL_V1"):
    """Train the compact 1D CNN on the same locked arrays as the baselines."""
    from training.train_ecg_cnn import train_cnn

    train_x, train_y = data["train"]
    val_x, val_y = data["val"]
    test_x, test_y = data["test"]
    cnn_dir = output_dir / f"ecg_cnn_{model_version}"
    train_cnn(
        train_x, train_y, val_x, val_y, test_x, test_y,
        experiment_dir=str(cnn_dir), dataset=dataset, seed=seed,
        max_epochs=epochs, batch_size=batch_size, lr=lr, patience=patience,
        model_version=model_version,
    )
    with (cnn_dir / "run_metadata.json").open("w") as handle:
        json.dump({"experiment": f"ecg_cnn_{model_version}", "model_version": model_version, "dataset": dataset,
                   "seed": seed, "git_commit": _git_revision(),
                   "preprocessing_artifact": str(output_dir / "preprocessing.json")},
                  handle, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ptbxl", default="data/raw/ptbxl")
    parser.add_argument("--manifest", default="data/manifests/ptbxl_manifest.csv")
    parser.add_argument("--split-manifest", default="data/splits/ptbxl_splits.csv")
    parser.add_argument("--output-dir", default="experiments/ptbxl_phase3")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--max-train-fit-records", type=int, default=None)
    parser.add_argument("--models", choices=["classical", "cnn", "all"], default="all")
    parser.add_argument("--cnn-epochs", type=int, default=30)
    parser.add_argument("--cnn-batch-size", type=int, default=32)
    parser.add_argument("--cnn-lr", type=float, default=0.001)
    parser.add_argument("--cnn-patience", type=int, default=7)
    parser.add_argument("--model-version", default="MODEL_V1")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    dataset = PTBXLDataset(data_dir=args.ptbxl, dataset_version="1.0.1")
    if not dataset.is_available():
        raise SystemExit(f"PTB-XL is unavailable at {args.ptbxl}")
    manifest = load_locked_manifest(
        dataset, Path(args.manifest), Path(args.split_manifest), args.seed, args.max_records
    )
    data, _ = materialize_windows(
        dataset, manifest, Path(args.output_dir), args.max_train_fit_records
    )
    if any(len(data[s][1]) == 0 for s in ("train", "val", "test")):
        raise SystemExit("Every split must contain windows before research baselines can run")
    output_dir = Path(args.output_dir)
    if args.models in ("classical", "all"):
        run_classical(data, output_dir, "ptbxl", args.seed)
    if args.models in ("cnn", "all"):
        run_cnn(data, output_dir, "ptbxl", args.seed, args.cnn_epochs, args.cnn_batch_size,
                args.cnn_lr, args.cnn_patience, args.model_version)


if __name__ == "__main__":
    main()
