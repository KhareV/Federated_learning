"""
training/train_classical.py — Classical ECG Baseline Models
============================================================
Trains and evaluates:
  E01: Majority/trivial classifier
  E02: Logistic Regression
  E03: Random Forest

Uses the P1 ECG feature library for feature extraction.
All experiments use the patient-level split manifest.

Usage (with synthetic data for development):
  python training/train_classical.py --synthetic

Usage (with PTB-XL after download):
  python training/train_classical.py --ptbxl data/raw/ptbxl

Outputs saved to:
  experiments/E01_majority/
  experiments/E02_logistic/
  experiments/E03_random_forest/
"""

import sys
import os
import json
import logging
import argparse
import time
from pathlib import Path

import numpy as np
import joblib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.ecg import ECGPreprocessor, NormalizationStats, synthesize_ecg_segment
from preprocessing.windowing import ECGWindower
from preprocessing.quality_ecg import ECGQualityAssessor
from features.ecg_features import ECGFeatureExtractor
from evaluation.metrics import compute_metrics, compute_per_class_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Synthetic Data Generator (for development/CI without real dataset) ───────

def generate_synthetic_dataset(
    n_normal: int = 300,
    n_abnormal: int = 200,
    window_samples: int = 2500,
    fs: int = 250,
    seed: int = 42,
):
    """
    Generate synthetic ECG windows for development/testing.

    NOT for reporting research results. Only for pipeline testing.
    Results from this function are clearly marked SYNTHETIC.
    """
    rng = np.random.RandomState(seed)
    signals, labels, participant_ids = [], [], []

    # Generate normal beats (clean, low noise)
    for i in range(n_normal):
        noise = rng.uniform(0.02, 0.08)
        sig = synthesize_ecg_segment(window_samples, fs, noise_std=noise, rng=rng)
        signals.append(sig)
        labels.append(0)  # NORMAL
        participant_ids.append(f"SYN_N_{i:04d}")

    # Generate "abnormal" beats (high noise / altered morphology)
    for i in range(n_abnormal):
        noise = rng.uniform(0.15, 0.40)
        hr = rng.uniform(100, 140)  # Tachycardic
        sig = synthesize_ecg_segment(
            window_samples, fs, heart_rate_bpm=hr, noise_std=noise, rng=rng
        )
        signals.append(sig)
        labels.append(1)  # ABNORMAL
        participant_ids.append(f"SYN_A_{i:04d}")

    return np.array(signals), np.array(labels), participant_ids


def patient_level_split_synthetic(participant_ids, labels, val_frac=0.15,
                                   test_frac=0.15, seed=42):
    """Split synthetic data by participant ID (deterministic)."""
    rng = np.random.RandomState(seed)
    unique_pids = np.array(sorted(set(participant_ids)))
    rng.shuffle(unique_pids)

    n = len(unique_pids)
    n_test = max(1, int(np.ceil(n * test_frac)))
    n_val = max(1, int(np.ceil(n * val_frac)))

    test_pids = set(unique_pids[-n_test:])
    val_pids = set(unique_pids[-(n_test + n_val):-n_test])
    train_pids = set(unique_pids[:-(n_test + n_val)])

    splits = {"train": [], "val": [], "test": []}
    for idx, pid in enumerate(participant_ids):
        if pid in test_pids:
            splits["test"].append(idx)
        elif pid in val_pids:
            splits["val"].append(idx)
        else:
            splits["train"].append(idx)

    # Leakage check
    assert len(train_pids & val_pids) == 0
    assert len(train_pids & test_pids) == 0
    assert len(val_pids & test_pids) == 0

    return splits


# ─── Feature Extraction ───────────────────────────────────────────────────────

def extract_features(
    signals: np.ndarray,
    labels: np.ndarray,
    preprocessor: ECGPreprocessor,
    feature_extractor: ECGFeatureExtractor,
    quality_assessor: ECGQualityAssessor,
    source_fs: int = 250,
    split_name: str = "unknown",
) -> tuple:
    """
    Preprocess → assess SQI → extract features for a batch of signals.
    Returns (X, y, sqi_scores).
    """
    X, y, sqi_scores = [], [], []

    for i, (sig, label) in enumerate(zip(signals, labels)):
        # Preprocess
        prep = preprocessor.process(sig, source_fs, record_id=f"{split_name}_{i}")
        if not prep.is_valid:
            continue

        # SQI
        sqi = quality_assessor.assess(prep.signal)

        # Features
        fs = feature_extractor.extract(
            prep.signal, record_id=f"{split_name}_{i}",
            sqi_overall=sqi.overall_sqi
        )

        X.append(fs.feature_values)
        y.append(label)
        sqi_scores.append(sqi.overall_sqi)

    return np.array(X), np.array(y), np.array(sqi_scores)


# ─── Experiment Runners ───────────────────────────────────────────────────────

def run_majority_baseline(
    y_train: np.ndarray,
    y_val: np.ndarray,
    y_test: np.ndarray,
    experiment_dir: str,
    dataset: str = "synthetic",
):
    """E01: Majority class classifier."""
    exp_dir = Path(experiment_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)

    majority_class = int(np.bincount(y_train).argmax())
    logger.info(f"E01 Majority class: {majority_class} "
                f"({'NORMAL' if majority_class == 0 else 'ABNORMAL'})")

    results = {}
    for split_name, y_split in [("val", y_val), ("test", y_test)]:
        y_pred = np.full(len(y_split), majority_class, dtype=int)
        metrics = compute_metrics(
            y_split, y_pred,
            split=split_name, model_name="majority_baseline",
            dataset=dataset,
            notes=f"Predicts class {majority_class} for all inputs"
        )
        metrics.print_report(f"E01 Majority Baseline — {split_name.upper()}")
        results[split_name] = metrics.to_dict()

    # Save results
    with open(exp_dir / "results.json", "w") as f:
        json.dump({
            "experiment": "E01_majority_baseline",
            "majority_class": majority_class,
            "dataset": dataset,
            "results": results,
        }, f, indent=2)

    logger.info(f"E01 results saved to {exp_dir}")
    return results


def run_logistic_regression(
    X_train, y_train, X_val, y_val, X_test, y_test,
    experiment_dir: str,
    dataset: str = "synthetic",
    seed: int = 42,
):
    """E02: Logistic Regression baseline."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    exp_dir = Path(experiment_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)

    # Scale features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    logger.info("Training Logistic Regression...")
    t0 = time.time()
    clf = LogisticRegression(
        max_iter=1000, C=1.0,
        class_weight="balanced",
        random_state=seed, solver="lbfgs",
    )
    clf.fit(X_train_s, y_train)
    train_time = time.time() - t0
    logger.info(f"LR trained in {train_time:.2f}s")

    results = {}
    for split_name, X_s, y_s in [
        ("val", X_val_s, y_val),
        ("test", X_test_s, y_test),
    ]:
        y_pred = clf.predict(X_s)
        y_prob = clf.predict_proba(X_s)[:, 1]
        metrics = compute_metrics(
            y_s, y_pred, y_prob,
            split=split_name, model_name="logistic_regression",
            dataset=dataset,
        )
        metrics.print_report(f"E02 Logistic Regression — {split_name.upper()}")
        results[split_name] = metrics.to_dict()

    # Save model + results
    joblib.dump(clf, exp_dir / "model.pkl")
    joblib.dump(scaler, exp_dir / "scaler.pkl")
    with open(exp_dir / "results.json", "w") as f:
        json.dump({
            "experiment": "E02_logistic_regression",
            "training_time_s": round(train_time, 2),
            "n_features": X_train.shape[1],
            "dataset": dataset,
            "seed": seed,
            "results": results,
        }, f, indent=2)

    logger.info(f"E02 results saved to {exp_dir}")
    return results, clf, scaler


def run_random_forest(
    X_train, y_train, X_val, y_val, X_test, y_test,
    experiment_dir: str,
    dataset: str = "synthetic",
    seed: int = 42,
    n_estimators: int = 200,
):
    """E03: Random Forest baseline."""
    from sklearn.ensemble import RandomForestClassifier

    exp_dir = Path(experiment_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Training Random Forest ({n_estimators} trees)...")
    t0 = time.time()
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=12,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)
    train_time = time.time() - t0
    logger.info(f"RF trained in {train_time:.2f}s")

    results = {}
    for split_name, X_s, y_s in [
        ("val", X_val, y_val),
        ("test", X_test, y_test),
    ]:
        y_pred = clf.predict(X_s)
        y_prob = clf.predict_proba(X_s)[:, 1]
        metrics = compute_metrics(
            y_s, y_pred, y_prob,
            split=split_name, model_name="random_forest",
            dataset=dataset,
        )
        metrics.print_report(f"E03 Random Forest — {split_name.upper()}")
        results[split_name] = metrics.to_dict()

    # Feature importance
    importances = clf.feature_importances_
    feat_names = ECGFeatureExtractor(fs=250).FEATURE_NAMES
    top_feats = sorted(zip(feat_names, importances), key=lambda x: -x[1])[:10]
    logger.info("Top 10 features by RF importance:")
    for name, imp in top_feats:
        logger.info(f"  {imp:.4f}  {name}")

    # Save
    joblib.dump(clf, exp_dir / "model.pkl")
    with open(exp_dir / "results.json", "w") as f:
        json.dump({
            "experiment": "E03_random_forest",
            "training_time_s": round(train_time, 2),
            "n_estimators": n_estimators,
            "n_features": X_train.shape[1],
            "dataset": dataset,
            "seed": seed,
            "top_features": [(n, round(float(v), 4)) for n, v in top_feats],
            "results": results,
        }, f, indent=2)

    logger.info(f"E03 results saved to {exp_dir}")
    return results, clf


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="P1 Classical Baseline Training"
    )
    parser.add_argument("--synthetic", action="store_true",
                        help="Use synthetic data (no dataset download needed)")
    parser.add_argument("--ptbxl", type=str, default=None,
                        help="Path to PTB-XL dataset root")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="experiments")
    parser.add_argument("--n-normal", type=int, default=300)
    parser.add_argument("--n-abnormal", type=int, default=200)
    args = parser.parse_args()

    np.random.seed(args.seed)

    preprocessor = ECGPreprocessor()
    feature_extractor = ECGFeatureExtractor(fs=250)
    quality_assessor = ECGQualityAssessor()
    windower = ECGWindower()

    # ── Load data ────────────────────────────────────────────────────────────
    if args.ptbxl:
        logger.info(f"Loading PTB-XL from {args.ptbxl}...")
        from datasets.ptbxl import PTBXLDataset
        dataset_obj = PTBXLDataset(data_dir=args.ptbxl)
        if not dataset_obj.is_available():
            logger.error("PTB-XL not found. Use --synthetic for demo.")
            sys.exit(1)
        manifest = dataset_obj.build_manifest()
        manifest = dataset_obj.generate_splits(manifest, seed=args.seed)

        all_signals, all_labels, all_pids = [], [], []
        for split in ["train", "val", "test"]:
            split_rows = dataset_obj.get_split_records(manifest, split)
            for _, row in split_rows.iterrows():
                try:
                    rec_obj = None
                    for r in dataset_obj.load_all_records():
                        if r.record_id == row["record_id"]:
                            rec_obj = r
                            break
                    if rec_obj is None:
                        continue
                    sig, fs = dataset_obj.load_signal(rec_obj)
                    all_signals.append(sig[:12500] if len(sig) > 12500 else sig)
                    all_labels.append(int(row["label_int"]))
                    all_pids.append(row["participant_id"])
                except Exception as exc:
                    logger.warning(f"Skip {row['record_id']}: {exc}")

        signals = np.array(all_signals)
        labels = np.array(all_labels)
        participant_ids = all_pids
        dataset_name = "ptbxl"
        source_fs = 500
    else:
        logger.info(
            "Using SYNTHETIC data for development. "
            "NOT for reporting research results."
        )
        signals, labels, participant_ids = generate_synthetic_dataset(
            n_normal=args.n_normal, n_abnormal=args.n_abnormal, seed=args.seed
        )
        dataset_name = "SYNTHETIC"
        source_fs = 250

    logger.info(
        f"Dataset: {len(signals)} signals, "
        f"NORMAL={sum(labels==0)}, ABNORMAL={sum(labels==1)}"
    )

    # ── Patient-level split ───────────────────────────────────────────────────
    splits = patient_level_split_synthetic(
        participant_ids, labels, seed=args.seed
    )
    logger.info(
        f"Splits: train={len(splits['train'])}, "
        f"val={len(splits['val'])}, test={len(splits['test'])}"
    )

    # ── Feature extraction ────────────────────────────────────────────────────
    logger.info("Extracting features...")

    train_idx, val_idx, test_idx = splits["train"], splits["val"], splits["test"]

    X_train, y_train, _ = extract_features(
        signals[train_idx], labels[train_idx],
        preprocessor, feature_extractor, quality_assessor,
        source_fs=source_fs, split_name="train"
    )
    X_val, y_val, _ = extract_features(
        signals[val_idx], labels[val_idx],
        preprocessor, feature_extractor, quality_assessor,
        source_fs=source_fs, split_name="val"
    )
    X_test, y_test, _ = extract_features(
        signals[test_idx], labels[test_idx],
        preprocessor, feature_extractor, quality_assessor,
        source_fs=source_fs, split_name="test"
    )

    logger.info(
        f"Features: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}"
    )

    # ── Run experiments ───────────────────────────────────────────────────────
    outdir = args.output_dir

    run_majority_baseline(
        y_train, y_val, y_test,
        f"{outdir}/E01_majority",
        dataset=dataset_name,
    )

    run_logistic_regression(
        X_train, y_train, X_val, y_val, X_test, y_test,
        f"{outdir}/E02_logistic",
        dataset=dataset_name, seed=args.seed,
    )

    run_random_forest(
        X_train, y_train, X_val, y_val, X_test, y_test,
        f"{outdir}/E03_random_forest",
        dataset=dataset_name, seed=args.seed,
    )

    logger.info("=" * 60)
    logger.info("Classical baselines complete. Check experiments/E0{1,2,3}_*/")
    logger.info("Next: python training/train_ecg_cnn.py --synthetic")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
