"""Phase 4 evaluation for calibrated MODEL_V1, MIT-BIH, and noise stress."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy.io import loadmat
from sklearn.metrics import brier_score_loss

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calibration.temperature import TemperatureScaler, select_f1_threshold
from datasets.mitbih import MITBIHDataset
from evaluation.metrics import compute_metrics, grouped_bootstrap_confidence_intervals
from evaluation.release_gate import ExternalReleaseGate
from models.ecg_cnn import ECGCNN1D
from preprocessing.ecg import ECGPreprocessor
from preprocessing.quality_ecg import ECGQualityAssessor
from training.run_ptbxl_baselines import load_locked_manifest, materialize_windows
from datasets.ptbxl import PTBXLDataset

logger = logging.getLogger("phase4")


def predict(model, signals, batch_size=256):
    model.eval()
    values = []
    with torch.no_grad():
        for start in range(0, len(signals), batch_size):
            batch = torch.from_numpy(np.asarray(signals[start:start + batch_size], dtype=np.float32))
            logits = model(batch.unsqueeze(1))
            values.extend(torch.softmax(logits, dim=1)[:, 1].cpu().numpy())
    return np.asarray(values, dtype=float)


def evaluate_locked(model, data, calibrator, threshold, dataset_name, model_version):
    output = {}
    for split in ("val", "test"):
        signals, labels = data[split]
        raw = predict(model, signals)
        probabilities = calibrator.transform(raw)
        predictions = (probabilities >= threshold).astype(int)
        output[split] = compute_metrics(
            labels, predictions, probabilities, split=split,
            model_name=f"calibrated_{model_version}", dataset=dataset_name,
        ).to_dict()
        output[split]["brier_score"] = round(float(brier_score_loss(labels, probabilities)), 6)
    return output


def evaluate_mitbih(model, preprocessor, assessor, data_dir, threshold, model_version):
    dataset = MITBIHDataset(data_dir=data_dir)
    windows = dataset.build_windows(window_seconds=10, stride_seconds=5, target_fs=250)
    records = {r.record_id: r for r in dataset.load_all_records() if r.is_valid}
    transformed_records = {}
    signals, labels, groups = [], [], []
    for row in windows.itertuples():
        if row.record_id not in transformed_records:
            raw, fs, _, _ = dataset.load_signal_with_annotations(row.record_id)
            transformed_records[row.record_id] = preprocessor.transform(raw, fs, row.record_id, "mitbih").signal
        transformed_signal = transformed_records[row.record_id]
        window = transformed_signal[row.start_sample:row.end_sample]
        if len(window) == 2500 and assessor.assess(window).is_usable:
            signals.append(window)
            labels.append(int(row.label_int))
            groups.append(row.record_id)
    probabilities = predict(model, np.asarray(signals, dtype=np.float32))
    predictions = (probabilities >= threshold).astype(int)
    metrics = compute_metrics(
        np.asarray(labels), predictions, probabilities, split="external",
        model_name=f"calibrated_{model_version}", dataset="mitbih",
        notes="External validation only; no tuning or retraining.",
    ).to_dict()
    metrics["record_bootstrap_95ci"] = grouped_bootstrap_confidence_intervals(
        np.asarray(labels), predictions, probabilities, np.asarray(groups)
    )
    return metrics, len(signals)


def evaluate_noise(model, preprocessor, assessor, data_dir, threshold):
    by_snr = defaultdict(lambda: {"probabilities": [], "sqi": [], "unreliable": 0, "windows": 0, "quality_states": defaultdict(int)})
    for path in sorted(Path(data_dir).glob("*.mat")):
        record = loadmat(path)["data"][0, 0]
        snr = int(float(np.asarray(record["snr"]).squeeze()))
        fs = int(float(np.asarray(record["Fs"]).squeeze()))
        signal = np.asarray(record["noisy_ecg"], dtype=np.float32)
        signal = signal[:, 0] if signal.ndim == 2 else signal.squeeze()
        transformed = preprocessor.transform(signal, fs, path.stem, "mitbih_noise_stress")
        bucket = by_snr[snr]
        windows = [transformed.signal[start:start + 2500] for start in range(0, len(transformed.signal) - 2499, 1250)]
        usable = []
        for window in windows:
            quality = assessor.assess(window)
            bucket["windows"] += 1
            bucket["sqi"].append(quality.overall_sqi)
            bucket["quality_states"][quality.canonical_state] += 1
            if quality.is_usable:
                usable.append(window)
            else:
                bucket["unreliable"] += 1
        if usable:
            bucket["probabilities"].extend(predict(model, np.asarray(usable, dtype=np.float32)))
    result = {}
    for snr, bucket in sorted(by_snr.items(), reverse=True):
        probabilities = np.asarray(bucket["probabilities"])
        result[str(snr)] = {
            "n_windows": bucket["windows"],
            "n_usable": len(probabilities),
            "unreliable_fraction": bucket["unreliable"] / max(bucket["windows"], 1),
            "mean_sqi": float(np.mean(bucket["sqi"])) if bucket["sqi"] else 0.0,
            "predicted_abnormal_fraction": float(np.mean(probabilities >= threshold)) if len(probabilities) else 0.0,
            "mean_probability_abnormal": float(np.mean(probabilities)) if len(probabilities) else None,
            "probability_standard_deviation": float(np.std(probabilities)) if len(probabilities) else None,
            "quality_state_counts": dict(bucket["quality_states"]),
            "labels_available": False,
            "note": "Noise Stress Test labels are not compatible with the supervised binary target; classification metrics are intentionally not reported. Quality state and prediction stability are reported instead.",
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="experiments/ptbxl_phase3/ecg_cnn_MODEL_V1/best_checkpoint.pt")
    parser.add_argument("--preprocessing", default="experiments/ptbxl_phase3/preprocessing.json")
    parser.add_argument("--output-dir", default="experiments/ptbxl_phase4")
    parser.add_argument("--ptbxl", default="data/raw/ptbxl")
    parser.add_argument("--mitbih", default="data/raw/mitbih")
    parser.add_argument("--noise", default="data/raw/mitbih_noise_stress")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model, checkpoint = ECGCNN1D.load_checkpoint(args.model, device="cpu")
    model_version = checkpoint["config"]["model_version"]
    preprocessor = ECGPreprocessor.load_normalization_stats(args.preprocessing)
    assessor = ECGQualityAssessor(fs=250)

    ptbxl = PTBXLDataset(data_dir=args.ptbxl, dataset_version="1.0.1")
    manifest = load_locked_manifest(ptbxl, Path("data/manifests/ptbxl_manifest.csv"), Path("data/splits/ptbxl_splits.csv"), args.seed)
    data, _ = materialize_windows(ptbxl, manifest, output / "ptbxl_replay")
    val_raw = predict(model, data["val"][0])
    calibrator = TemperatureScaler().fit(val_raw, data["val"][1])
    threshold = select_f1_threshold(calibrator.transform(val_raw), data["val"][1])
    calibrator.save(output / "temperature_scaling.json")
    (output / "threshold.json").write_text(json.dumps({"threshold": threshold, "selection": "validation_max_f1_then_sensitivity"}, indent=2) + "\n")
    report = {
        "model_version": model_version,
        "calibration": calibrator.to_dict(),
        "threshold": threshold,
        "ptbxl": evaluate_locked(model, data, calibrator, threshold, "ptbxl", model_version),
    }
    report["mitbih"], report["mitbih_n_windows"] = evaluate_mitbih(
        model, preprocessor, assessor, args.mitbih, threshold, model_version
    )
    report["external_release_gate"] = ExternalReleaseGate().evaluate(report["mitbih"])
    report["release_status"] = "ELIGIBLE" if report["external_release_gate"]["status"] == "PASS" else "BLOCKED_EXTERNAL_GATE"
    report["noise_stress"] = evaluate_noise(model, preprocessor, assessor, args.noise, threshold)
    (output / "phase4_report.json").write_text(json.dumps(report, indent=2) + "\n")
    logger.info("Phase 4 report written to %s", output)


if __name__ == "__main__":
    main()
