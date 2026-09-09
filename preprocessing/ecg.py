"""
preprocessing/ecg.py — Canonical ECG Preprocessing Pipeline
============================================================
Preprocessing version: controlled by configs/ecg_preprocessing.yaml

Pipeline stages (all deterministic, zero-phase filtering):
  1. Input validation
  2. Resampling to canonical rate (250 Hz)
  3. Baseline wander removal (0.5 Hz highpass, Butterworth order 4)
  4. Band-limiting (0.5–40 Hz bandpass, Butterworth order 4)
  5. Powerline notch (50 Hz / 60 Hz, IIR notch Q=30)
  6. Z-score normalization (statistics from training data only)
  7. Amplitude clipping (±5σ by default)

IMPORTANT: Normalization statistics (mean, std) MUST come from training data.
Never fit normalization on validation or test data.

This module is the single canonical preprocessing path for:
  - PTB-XL
  - MIT-BIH
  - AD8232/ESP32 wearable data
Do NOT create separate pipelines for different datasets.
"""

import logging
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
from scipy import signal as scipy_signal

logger = logging.getLogger(__name__)

# ─── Preprocessing Version ────────────────────────────────────────────────────
PREPROCESSING_VERSION = "1.0.0"
TARGET_FS = 250  # Hz — canonical sampling rate


# ─── Result Dataclass ─────────────────────────────────────────────────────────

@dataclass
class PreprocessedECG:
    """
    Output of the canonical ECG preprocessing pipeline.
    All fields are deterministic given the same input and config.
    """
    signal: np.ndarray              # Preprocessed signal (float32)
    sampling_rate: int              # Always TARGET_FS after preprocessing
    original_sampling_rate: int     # Source fs
    n_samples: int
    preprocessing_version: str
    source_record_id: str
    source_dataset: str
    was_resampled: bool
    normalization_mean: float       # Mean used for z-score (from training)
    normalization_std: float        # Std used for z-score (from training)
    is_valid: bool = True
    validation_notes: list = None

    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []


# ─── Normalization Statistics ─────────────────────────────────────────────────

@dataclass
class NormalizationStats:
    """
    Normalization statistics derived from the training split only.
    Must be serialized and reused for val/test/inference.
    """
    mean: float
    std: float
    n_samples_used: int
    preprocessing_version: str = PREPROCESSING_VERSION

    @classmethod
    def from_signals(cls, signals: list, preprocessing_version: str = PREPROCESSING_VERSION):
        """Fit from a list of 1D numpy arrays (training signals only)."""
        all_values = np.concatenate([s.flatten() for s in signals])
        return cls(
            mean=float(np.mean(all_values)),
            std=float(np.std(all_values) + 1e-8),
            n_samples_used=len(all_values),
            preprocessing_version=preprocessing_version,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean,
            "std": self.std,
            "n_samples_used": self.n_samples_used,
            "preprocessing_version": self.preprocessing_version,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NormalizationStats":
        return cls(**d)


# ─── Preprocessing Pipeline ───────────────────────────────────────────────────

class ECGPreprocessor:
    """
    Canonical deterministic ECG preprocessing pipeline.

    All filters use zero-phase (filtfilt) implementation to avoid
    phase distortion that could affect morphology-based classification.

    Parameters
    ----------
    target_fs : int
        Canonical output sampling rate (default 250 Hz).
    bandpass_low : float
        Low cutoff for bandpass filter in Hz (default 0.5).
    bandpass_high : float
        High cutoff for bandpass filter in Hz (default 40.0).
    notch_freq : float
        Powerline notch frequency in Hz (50 for EU/India, 60 for US).
    notch_q : float
        Quality factor for notch filter.
    clip_std_multiplier : float
        Clip values beyond ±N×std after normalization.
    normalization_stats : NormalizationStats, optional
        Pre-fitted stats from training data. If None, per-signal z-score is used
        (only acceptable when computing training statistics, not during eval).
    """

    def __init__(
        self,
        target_fs: int = 250,
        bandpass_low: float = 0.5,
        bandpass_high: float = 40.0,
        notch_freq: float = 50.0,
        notch_q: float = 30.0,
        clip_std_multiplier: float = 5.0,
        normalization_stats: Optional[NormalizationStats] = None,
        filter_order: int = 4,
    ):
        self.target_fs = target_fs
        self.bandpass_low = bandpass_low
        self.bandpass_high = bandpass_high
        self.notch_freq = notch_freq
        self.notch_q = notch_q
        self.clip_std_multiplier = clip_std_multiplier
        self.normalization_stats = normalization_stats
        self.filter_order = filter_order
        self._preprocessing_version = PREPROCESSING_VERSION

        # Pre-compute filter coefficients at target_fs for efficiency
        self._bp_sos = self._make_bandpass_sos(target_fs)
        self._notch_b, self._notch_a = self._make_notch_ba(target_fs)

    @property
    def is_fitted(self) -> bool:
        """Whether frozen training-only normalization statistics are loaded."""
        return self.normalization_stats is not None

    def fit(self, training_signals: list, source_fs: int = TARGET_FS) -> "ECGPreprocessor":
        """Fit normalization statistics using training signals only.

        Filtering and resampling happen before fitting, so the statistics match
        the representation consumed by the model. Validation, test, and
        inference data must only use :meth:`transform` after this call.
        """
        if not training_signals:
            raise ValueError("At least one training signal is required")
        canonical = [self._prepare_signal(sig, source_fs) for sig in training_signals]
        canonical = [sig for sig in canonical if len(sig) > 0 and np.isfinite(sig).all()]
        if not canonical:
            raise ValueError("Training signals contain no valid samples")
        self.normalization_stats = NormalizationStats.from_signals(canonical)
        return self

    def save_normalization_stats(self, path) -> None:
        """Persist frozen training statistics as an auditable JSON artifact."""
        if not self.is_fitted:
            raise RuntimeError("Fit the preprocessor before saving statistics")
        payload = {"config": self.config_dict, "normalization": self.normalization_stats.to_dict()}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    @classmethod
    def load_normalization_stats(cls, path, **kwargs) -> "ECGPreprocessor":
        """Load a preprocessor with frozen statistics; never refits them."""
        payload = json.loads(Path(path).read_text())
        stats_payload = payload.get("normalization", payload)
        return cls(normalization_stats=NormalizationStats.from_dict(stats_payload), **kwargs)

    # ── Filter Coefficient Computation ───────────────────────────────────────

    def _make_bandpass_sos(self, fs: int):
        """
        Butterworth bandpass SOS coefficients.
        Using SOS form for numerical stability.
        """
        nyq = fs / 2.0
        low = self.bandpass_low / nyq
        high = self.bandpass_high / nyq
        # Clamp to valid range
        low = np.clip(low, 1e-4, 0.99)
        high = np.clip(high, low + 1e-4, 0.99)
        return scipy_signal.butter(
            self.filter_order, [low, high], btype="band", output="sos"
        )

    def _make_notch_ba(self, fs: int):
        """IIR notch filter coefficients."""
        return scipy_signal.iirnotch(self.notch_freq, self.notch_q, fs)

    # ── Resampling ────────────────────────────────────────────────────────────

    def resample(self, sig: np.ndarray, source_fs: int) -> np.ndarray:
        """
        Resample signal from source_fs to target_fs using polyphase filter.
        Returns float32.
        """
        if source_fs == self.target_fs:
            return sig.astype(np.float32)

        from fractions import Fraction
        ratio = Fraction(self.target_fs, source_fs).limit_denominator(100)
        up = ratio.numerator
        down = ratio.denominator
        resampled = scipy_signal.resample_poly(sig, up, down)
        return resampled.astype(np.float32)

    def _prepare_signal(self, raw_signal: np.ndarray, source_fs: int) -> np.ndarray:
        """Validate, resample, and filter without normalization."""
        sig = np.asarray(raw_signal, dtype=np.float32).flatten()
        if len(sig) == 0:
            return sig
        if not np.isfinite(sig).all():
            sig = np.where(np.isfinite(sig), sig, 0.0).astype(np.float32)
        if source_fs <= 0:
            raise ValueError("source_fs must be positive")
        if source_fs != self.target_fs:
            sig = self.resample(sig, source_fs)
        try:
            sig = self.apply_bandpass(sig)
        except Exception as exc:
            logger.warning("Bandpass failed during preparation: %s", exc)
        try:
            sig = self.apply_notch(sig)
        except Exception as exc:
            logger.warning("Notch failed during preparation: %s", exc)
        return sig.astype(np.float32)

    def transform(
        self, raw_signal: np.ndarray, source_fs: int,
        record_id: str = "unknown", source_dataset: str = "unknown",
    ) -> PreprocessedECG:
        """Transform a signal using frozen training statistics.

        This is the required validation/test/inference entry point and refuses
        to perform per-signal normalization when the preprocessor is unfitted.
        """
        if not self.is_fitted:
            raise RuntimeError("ECGPreprocessor must be fit on training data before transform")
        return self._process(raw_signal, source_fs, record_id, source_dataset)

    # ── Individual Filter Steps ───────────────────────────────────────────────

    def apply_bandpass(self, sig: np.ndarray, fs: Optional[int] = None) -> np.ndarray:
        """
        Zero-phase Butterworth bandpass filter (0.5–40 Hz).
        Handles baseline wander removal (highpass) and anti-aliasing (lowpass)
        in a single step.
        """
        if fs is not None and fs != self.target_fs:
            sos = self._make_bandpass_sos(fs)
        else:
            sos = self._bp_sos

        # Ensure minimum signal length for filtfilt
        min_len = 3 * self.filter_order + 1
        if len(sig) < min_len:
            raise ValueError(
                f"Signal too short ({len(sig)} samples) for filter order "
                f"{self.filter_order}. Minimum: {min_len} samples."
            )

        return scipy_signal.sosfiltfilt(sos, sig).astype(np.float32)

    def apply_notch(self, sig: np.ndarray, fs: Optional[int] = None) -> np.ndarray:
        """Zero-phase IIR notch filter to remove powerline interference."""
        if fs is not None and fs != self.target_fs:
            b, a = self._make_notch_ba(fs)
        else:
            b, a = self._notch_b, self._notch_a

        return scipy_signal.filtfilt(b, a, sig).astype(np.float32)

    def normalize(self, sig: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """
        Z-score normalization.
        If normalization_stats are provided (from training): use them.
        Otherwise: compute per-signal (only use for computing training stats).

        Returns
        -------
        normalized_signal, mean_used, std_used
        """
        if self.normalization_stats is not None:
            mean = self.normalization_stats.mean
            std = self.normalization_stats.std
        else:
            mean = float(np.mean(sig))
            std = float(np.std(sig) + 1e-8)

        normalized = (sig - mean) / std
        return normalized.astype(np.float32), mean, std

    def clip(self, sig: np.ndarray) -> np.ndarray:
        """Clip values beyond ±clip_std_multiplier (assuming signal is already normalized)."""
        limit = self.clip_std_multiplier
        return np.clip(sig, -limit, limit).astype(np.float32)

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    def process(
        self,
        raw_signal: np.ndarray,
        source_fs: int,
        record_id: str = "unknown",
        source_dataset: str = "unknown",
    ) -> PreprocessedECG:
        """
        Run the complete canonical preprocessing pipeline.

        Parameters
        ----------
        raw_signal : np.ndarray (1D, float or int)
        source_fs : int — original sampling rate
        record_id : str — for traceability
        source_dataset : str — for traceability

        Returns
        -------
        PreprocessedECG
        """
        # Compatibility entry point for existing smoke tests and training code.
        # New code must call fit() once and transform() thereafter.
        if self.is_fitted:
            return self._process(raw_signal, source_fs, record_id, source_dataset)
        logger.warning("Using legacy per-signal normalization; fit before research use")
        return self._process(raw_signal, source_fs, record_id, source_dataset, allow_unfitted=True)

    def _process(
        self, raw_signal: np.ndarray, source_fs: int,
        record_id: str, source_dataset: str, allow_unfitted: bool = False,
    ) -> PreprocessedECG:
        # ── Step 0: Input validation ──────────────────────────────────────────
        issues = []
        sig = np.array(raw_signal, dtype=np.float32).flatten()

        if len(sig) == 0:
            return PreprocessedECG(
                signal=sig, sampling_rate=self.target_fs,
                original_sampling_rate=source_fs, n_samples=0,
                preprocessing_version=self._preprocessing_version,
                source_record_id=record_id, source_dataset=source_dataset,
                was_resampled=False, normalization_mean=0.0,
                normalization_std=1.0, is_valid=False,
                validation_notes=["Empty signal"],
            )

        # Replace NaN/Inf with interpolated values or zeros
        if not np.isfinite(sig).all():
            n_bad = int(np.sum(~np.isfinite(sig)))
            issues.append(f"Replaced {n_bad} NaN/Inf values with 0")
            sig = np.where(np.isfinite(sig), sig, 0.0)

        # ── Steps 1–3: Resample and filter ────────────────────────────────────
        was_resampled = source_fs != self.target_fs
        sig = self._prepare_signal(sig, source_fs)

        # ── Step 4: Normalize ─────────────────────────────────────────────────
        if not self.is_fitted and not allow_unfitted:
            raise RuntimeError("ECGPreprocessor must be fit before normalization")
        sig, norm_mean, norm_std = self.normalize(sig)

        # ── Step 5: Clip ──────────────────────────────────────────────────────
        sig = self.clip(sig)

        return PreprocessedECG(
            signal=sig,
            sampling_rate=self.target_fs,
            original_sampling_rate=source_fs,
            n_samples=len(sig),
            preprocessing_version=self._preprocessing_version,
            source_record_id=record_id,
            source_dataset=source_dataset,
            was_resampled=was_resampled,
            normalization_mean=norm_mean,
            normalization_std=norm_std,
            is_valid=True,
            validation_notes=issues,
        )

    @property
    def config_dict(self) -> Dict[str, Any]:
        """Serializable config for experiment tracking."""
        return {
            "preprocessing_version": self._preprocessing_version,
            "target_fs": self.target_fs,
            "bandpass_low": self.bandpass_low,
            "bandpass_high": self.bandpass_high,
            "notch_freq": self.notch_freq,
            "notch_q": self.notch_q,
            "clip_std_multiplier": self.clip_std_multiplier,
            "filter_order": self.filter_order,
            "normalization_fitted": self.is_fitted,
            "normalization_stats": self.normalization_stats.to_dict() if self.is_fitted else None,
        }


# ─── Synthetic ECG Generator (for testing) ───────────────────────────────────

def synthesize_ecg_segment(
    n_samples: int,
    fs: int = 250,
    heart_rate_bpm: float = 72.0,
    noise_std: float = 0.05,
    baseline_drift: float = 0.0,
    rng: Optional[np.random.RandomState] = None,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a synthetic ECG-like signal for pipeline testing.
    Uses Gaussian approximations of the PQRST complex.

    NOT intended for clinical use. Used only for unit tests.

    Parameters
    ----------
    n_samples : int
    fs : int — sampling rate in Hz
    heart_rate_bpm : float
    noise_std : float — Gaussian noise level in normalized units
    baseline_drift : float — amplitude of low-frequency baseline drift
    rng : np.random.RandomState, optional
    seed : int, optional

    Returns
    -------
    np.ndarray of float32, length n_samples
    """
    if rng is None:
        if seed is not None:
            rng = np.random.RandomState(seed)
        else:
            rng = np.random.RandomState(42)

    t = np.arange(n_samples) / fs
    rr_seconds = 60.0 / heart_rate_bpm

    sig = np.zeros(n_samples, dtype=np.float32)

    # PQRST Gaussian components (normalized)
    # Positions relative to R-peak (in seconds)
    pqrst = [
        # (offset_s, amplitude, width_s)
        (-0.20, 0.15, 0.025),   # P wave
        (-0.07, -0.05, 0.015),  # Q wave
        (0.00, 1.00, 0.012),    # R wave (dominant)
        (0.07, -0.15, 0.020),   # S wave
        (0.20, 0.25, 0.040),    # T wave
    ]

    # Place beats at regular intervals
    beat_time = rr_seconds / 2  # start half a beat in
    while beat_time < t[-1]:
        for offset, amp, width in pqrst:
            center = beat_time + offset
            wave = amp * np.exp(-0.5 * ((t - center) / width) ** 2)
            sig += wave.astype(np.float32)
        beat_time += rr_seconds

    # Add noise
    if noise_std > 0:
        sig += rng.normal(0, noise_std, n_samples).astype(np.float32)

    # Add baseline drift
    if baseline_drift > 0:
        drift_freq = 0.2  # Hz (typical respiratory frequency)
        drift = baseline_drift * np.sin(2 * np.pi * drift_freq * t)
        sig += drift.astype(np.float32)

    return sig
