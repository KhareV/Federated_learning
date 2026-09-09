"""Hosted centralized ECG research-candidate service loaded once per process."""

import time
import hashlib
import json
from pathlib import Path

import numpy as np

from calibration.temperature import TemperatureScaler
from models.ecg_cnn import ECGCNN1D
from preprocessing.ecg import ECGPreprocessor
from preprocessing.quality_ecg import ECGQualityAssessor


class ModelUnavailable(RuntimeError):
    pass


class ModelService:
    def __init__(self, model_path=None, preprocessing_path=None, calibration_path=None, lock_path=None):
        self.model_path = Path(model_path or "experiments/centralized_ecg_v2/ecg_cnn_MODEL_V2/best_checkpoint.pt")
        self.preprocessing_path = Path(preprocessing_path or "experiments/centralized_ecg_v2/preprocessing.json")
        self.calibration_path = Path(calibration_path or "experiments/centralized_ecg_v2_evaluation/temperature_scaling.json")
        self.lock_path = Path(lock_path or "artifacts/MODEL_V2_RESEARCH_CANDIDATE/LOCK_MANIFEST.json")
        self.model = None
        self.preprocessor = None
        self.calibrator = None
        self.threshold = 0.5
        self.model_version = "MODEL_V2"
        self.release_status = "RESEARCH_CANDIDATE_BLOCKED_EXTERNAL_GATE"
        self.artifact_integrity = "UNVERIFIED"

    def _verify_lock(self):
        if not self.lock_path.exists():
            raise ModelUnavailable("Central ECG candidate lock manifest is unavailable")
        lock = json.loads(self.lock_path.read_text())
        mismatches = []
        for name, item in lock["artifacts"].items():
            path = Path(item["path"])
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if actual != item["sha256"]:
                mismatches.append(name)
        if mismatches:
            raise ModelUnavailable(f"Central ECG candidate integrity verification failed: {', '.join(mismatches)}")
        self.artifact_integrity = "VERIFIED"

    def load(self):
        if not self.model_path.exists() or not self.preprocessing_path.exists():
            raise ModelUnavailable("Central ECG research-candidate artifacts are unavailable")
        self._verify_lock()
        self.model, checkpoint = ECGCNN1D.load_checkpoint(str(self.model_path), device="cpu")
        self.preprocessor = ECGPreprocessor.load_normalization_stats(self.preprocessing_path)
        if self.calibration_path.exists():
            self.calibrator = TemperatureScaler.load(self.calibration_path)
        threshold_path = self.calibration_path.parent / "threshold.json"
        if threshold_path.exists():
            import json
            self.threshold = float(json.loads(threshold_path.read_text())["threshold"])
        self.model_version = checkpoint["config"]["model_version"]
        return self

    @property
    def available(self):
        return self.model is not None and self.preprocessor is not None

    def predict_ecg(self, samples, source_fs=250):
        if not self.available:
            self.load()
        started = time.perf_counter()
        processed = self.preprocessor.transform(np.asarray(samples), source_fs, "api", "api")
        assessor = ECGQualityAssessor(fs=self.preprocessor.target_fs)
        quality = assessor.assess(processed.signal)
        if not quality.is_usable:
            return {"model_version": self.model_version, "prediction": "UNRELIABLE_SIGNAL",
                    "confidence": 0.0, "probability_abnormal": None,
                    "signal_quality": quality.canonical_state, "available_modalities": ["ECG"],
                    "model_mode": "ECG_ONLY", "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "disclaimer": "Research prototype; not a medical diagnosis."}
        signal = processed.signal[:2500]
        if len(signal) < 2500:
            signal = np.pad(signal, (0, 2500 - len(signal)))
        import torch
        with torch.no_grad():
            logits = self.model(torch.from_numpy(signal).float().view(1, 1, -1))
            probability = float(torch.softmax(logits, dim=1)[0, 1].item())
        if self.calibrator:
            probability = float(self.calibrator.transform([probability])[0])
        prediction = "POTENTIALLY_ABNORMAL" if probability >= self.threshold else "NORMAL_MONITORED_PATTERN"
        return {"model_version": self.model_version, "prediction": prediction,
                "confidence": round(max(probability, 1 - probability), 4),
                "probability_abnormal": round(probability, 4),
                "signal_quality": quality.canonical_state, "available_modalities": ["ECG"],
                "model_mode": "ECG_ONLY", "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "disclaimer": "Research prototype; not a medical diagnosis."}


model_service = ModelService()
