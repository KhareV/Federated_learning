"""
inference/ecg_inference.py — P1 Standardized ECG Inference Interface
======================================================================
Provides a single, stable inference interface for:
  - Backend API integration
  - Federated learning client (P3)
  - Multimodal fusion (P2)
  - Wearable device real-time inference

The interface is model-agnostic: it works with the frozen MODEL_V1
checkpoint (CNN) or any compatible model that exposes predict_proba().

Output format (ECGInferenceResult):
{
  "prediction": "NORMAL" | "ABNORMAL",
  "prediction_int": 0 | 1,
  "probability_normal": float,
  "probability_abnormal": float,
  "confidence": float,
  "signal_quality_score": float,   # SQI 0–100
  "signal_quality_state": str,     # EXCELLENT|GOOD|FAIR|POOR
  "model_version": str,            # e.g. "MODEL_V1"
  "model_type": str,               # e.g. "ecg_cnn_1d"
  "preprocessing_version": str,
  "source_dataset": str,
  "record_id": str,
  "window_samples": int,
  "sampling_rate": int,
  "timestamp": str,                # ISO 8601
  "disclaimer": str,               # Always included
}

P3 reliability metadata (for federated aggregation):
  Available via get_fl_reliability_metadata() — does NOT include raw signal.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "RESEARCH PROTOTYPE: This output is from an experimental AI model "
    "trained on synthetic/research data. It is NOT a medical diagnosis "
    "and should NOT be used for clinical decision-making."
)

CLASS_NAMES = {0: "NORMAL", 1: "ABNORMAL"}


# ─── Inference Result ─────────────────────────────────────────────────────────

@dataclass
class ECGInferenceResult:
    """
    Standardized P1 ECG inference output.
    This is the canonical output consumed by P2, P3, and the backend.
    """
    prediction: str                   # "NORMAL" or "ABNORMAL"
    prediction_int: int               # 0 or 1
    probability_normal: float         # P(NORMAL)
    probability_abnormal: float       # P(ABNORMAL)
    confidence: float                 # max(P(NORMAL), P(ABNORMAL))

    signal_quality_score: float       # SQI 0–100
    signal_quality_state: str         # EXCELLENT|GOOD|FAIR|POOR
    is_high_quality: bool             # SQI >= 60

    model_version: str                # e.g. "MODEL_V1"
    model_type: str                   # e.g. "ecg_cnn_1d"
    preprocessing_version: str        # e.g. "1.0.0"

    source_dataset: str               # "ptbxl" | "mitbih" | "wearable_ad8232"
    record_id: str                    # Source record/window identifier
    window_samples: int
    sampling_rate: int

    timestamp: str                    # ISO 8601 UTC
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_api_response(self) -> Dict[str, Any]:
        """Compact dict for backend API response (excludes disclaimer body)."""
        d = self.to_dict()
        d["disclaimer"] = "See full disclaimer in API docs"
        return d


# ─── Inference Engine ─────────────────────────────────────────────────────────

class ECGInferenceEngine:
    """
    P1 ECG inference engine.

    Wraps a trained model (CNN or classical) with the canonical
    preprocessing pipeline and SQI assessor.

    Parameters
    ----------
    model_path : str, optional
        Path to MODEL_V1 checkpoint (.pt for CNN, .pkl for classical).
        If None, uses a dummy model for pipeline testing.
    model_type : str
        "ecg_cnn_1d" | "logistic_regression" | "random_forest"
    preprocessing_version : str
        Must match the version used during training.
    device : str
        "cpu" | "cuda" | "auto"
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_type: str = "ecg_cnn_1d",
        model_version: str = "MODEL_V1",
        preprocessing_version: str = "1.0.0",
        device: str = "auto",
    ):
        self.model_path = model_path
        self.model_type = model_type
        self.model_version = model_version
        self.preprocessing_version = preprocessing_version

        import torch
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model = None
        self._scaler = None

        # Initialize preprocessing pipeline
        from preprocessing.ecg import ECGPreprocessor
        from preprocessing.quality_ecg import ECGQualityAssessor
        self._preprocessor = ECGPreprocessor()
        self._quality_assessor = ECGQualityAssessor()

        if model_path:
            self._load_model(model_path)
        else:
            logger.warning(
                "No model_path provided. Using dummy predictor for testing."
            )

    def _load_model(self, path: str):
        """Load model from checkpoint file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {path}")

        if self.model_type == "ecg_cnn_1d":
            from models.ecg_cnn import ECGCNN1D
            self._model, _ = ECGCNN1D.load_checkpoint(path, device=self.device)
            self._model.eval()
            logger.info(f"Loaded CNN from {path}")

        elif self.model_type in ("logistic_regression", "random_forest"):
            import joblib
            self._model = joblib.load(path)
            # Try to load paired scaler
            scaler_path = p.parent / "scaler.pkl"
            if scaler_path.exists():
                self._scaler = joblib.load(scaler_path)
                logger.info(f"Loaded scaler from {scaler_path}")
            logger.info(f"Loaded {self.model_type} from {path}")

        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

    # ── Core Inference ────────────────────────────────────────────────────────

    def predict(
        self,
        raw_signal: np.ndarray,
        source_fs: int,
        record_id: str = "unknown",
        source_dataset: str = "unknown",
        window_samples: int = 2500,
    ) -> ECGInferenceResult:
        """
        Run the complete P1 ECG inference pipeline.

        1. Preprocess signal (resample → bandpass → notch → normalize → clip)
        2. Assess signal quality (SQI)
        3. Run model inference
        4. Return standardized result

        Parameters
        ----------
        raw_signal : np.ndarray (1D) — raw ECG in any unit/scale
        source_fs : int — original sampling rate
        record_id : str — for traceability
        source_dataset : str — "ptbxl" | "mitbih" | "wearable_ad8232"
        window_samples : int — expected input length (will pad/trim)

        Returns
        -------
        ECGInferenceResult
        """
        import torch

        # Step 1: Preprocess
        prep = self._preprocessor.process(
            raw_signal, source_fs,
            record_id=record_id, source_dataset=source_dataset
        )

        # Step 2: SQI
        sqi_result = self._quality_assessor.assess(prep.signal)

        # Step 3: Prepare window
        signal_for_model = prep.signal
        if len(signal_for_model) >= window_samples:
            signal_for_model = signal_for_model[:window_samples]
        else:
            signal_for_model = np.pad(
                signal_for_model,
                (0, window_samples - len(signal_for_model)),
                mode="constant"
            )

        # Step 4: Inference
        if self._model is None:
            # Dummy predictor (for testing pipeline without trained model)
            prob_normal = 0.6 + np.random.uniform(-0.1, 0.1)
            prob_abnormal = 1.0 - prob_normal
        elif self.model_type == "ecg_cnn_1d":
            x = torch.tensor(
                signal_for_model, dtype=torch.float32
            ).unsqueeze(0).unsqueeze(0).to(self.device)  # (1, 1, n)
            probs = self._model.predict_proba(x)[0].cpu().numpy()
            prob_normal = float(probs[0])
            prob_abnormal = float(probs[1])
        else:
            # Classical model: extract features first
            from features.ecg_features import ECGFeatureExtractor
            extractor = ECGFeatureExtractor(fs=250)
            feat_set = extractor.extract(
                signal_for_model, record_id=record_id,
                sqi_overall=sqi_result.overall_sqi
            )
            X = feat_set.feature_values.reshape(1, -1)
            if self._scaler is not None:
                X = self._scaler.transform(X)
            probs = self._model.predict_proba(X)[0]
            prob_normal = float(probs[0])
            prob_abnormal = float(probs[1])

        # Determine prediction
        prediction_int = 1 if prob_abnormal >= prob_normal else 0
        prediction = CLASS_NAMES[prediction_int]
        confidence = max(prob_normal, prob_abnormal)

        return ECGInferenceResult(
            prediction=prediction,
            prediction_int=prediction_int,
            probability_normal=round(prob_normal, 4),
            probability_abnormal=round(prob_abnormal, 4),
            confidence=round(confidence, 4),
            signal_quality_score=round(sqi_result.overall_sqi, 2),
            signal_quality_state=sqi_result.quality_state,
            is_high_quality=sqi_result.overall_sqi >= 60,
            model_version=self.model_version,
            model_type=self.model_type,
            preprocessing_version=self.preprocessing_version,
            source_dataset=source_dataset,
            record_id=record_id,
            window_samples=int(window_samples),
            sampling_rate=self._preprocessor.target_fs,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def predict_batch(
        self,
        signals: list,
        source_fs: int,
        record_ids: Optional[list] = None,
        source_dataset: str = "unknown",
        window_samples: int = 2500,
    ) -> list:
        """Run inference on a batch of signals."""
        if record_ids is None:
            record_ids = [f"signal_{i}" for i in range(len(signals))]
        return [
            self.predict(sig, source_fs, rid, source_dataset, window_samples)
            for sig, rid in zip(signals, record_ids)
        ]

    # ── P3 FL Reliability Metadata ────────────────────────────────────────────

    def get_fl_reliability_metadata(
        self,
        signals: list,
        source_fs: int,
        client_id: str,
        local_f1: float = -1.0,
        local_loss: float = -1.0,
        battery_level: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Compute the reliability metadata needed by P3 (federated aggregation).

        IMPORTANT: Raw ECG signals are NOT included in this output.
        Only aggregate quality statistics and model metadata are provided.

        This satisfies the QAPFL requirement for:
          q_signal = mean(SQI)
          q_data   = usable_samples / total_samples
          q_model  = local_F1
          q_uncert = 1 - uncertainty

        Parameters
        ----------
        signals : list of np.ndarray — raw/processed ECG segments
        source_fs : int
        client_id : str
        local_f1 : float — local model F1 from last training round
        local_loss : float — local training loss
        battery_level : float — 0–1 (from device if available)

        Returns
        -------
        dict — no raw signals included
        """
        sqi_scores = []
        valid_count = 0

        for sig in signals:
            prep = self._preprocessor.process(sig, source_fs)
            if prep.is_valid:
                sqi = self._quality_assessor.assess(prep.signal)
                sqi_scores.append(sqi.overall_sqi)
                valid_count += 1

        total = len(signals)
        usable = valid_count
        sqi_arr = np.array(sqi_scores) if sqi_scores else np.array([0.0])

        # Uncertainty proxy: high confidence variance = high uncertainty
        results = self.predict_batch(
            signals[:min(50, len(signals))],  # Sample for speed
            source_fs=source_fs,
            source_dataset="local_client",
        )
        confidences = np.array([r.confidence for r in results])
        uncertainty_proxy = float(np.std(confidences))

        return {
            "client_id": client_id,
            "model_version": self.model_version,
            "preprocessing_version": self.preprocessing_version,
            "num_samples": total,
            "usable_sample_count": usable,
            "usable_sample_percentage": round(usable / max(total, 1) * 100, 2),
            "mean_sqi": round(float(np.mean(sqi_arr)), 2),
            "std_sqi": round(float(np.std(sqi_arr)), 2),
            "quality_distribution": {
                "EXCELLENT": int(np.sum(sqi_arr >= 80)),
                "GOOD": int(np.sum((sqi_arr >= 60) & (sqi_arr < 80))),
                "FAIR": int(np.sum((sqi_arr >= 40) & (sqi_arr < 60))),
                "POOR": int(np.sum(sqi_arr < 40)),
            },
            "local_f1": round(local_f1, 4),
            "local_loss": round(local_loss, 4),
            "mean_confidence": round(float(np.mean(confidences)), 4),
            "std_confidence": round(float(np.std(confidences)), 4),
            "uncertainty_proxy": round(uncertainty_proxy, 4),
            "battery_level": round(battery_level, 3),
            # raw_signals: intentionally NOT included (privacy boundary)
        }
