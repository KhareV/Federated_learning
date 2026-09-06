"""
preprocessing/quality_ecg.py — P1 ECG Signal Quality Index (SQI)
=================================================================
Standalone SQI module that wraps and extends the existing
backend/ml/signal_quality/ecg_sqi.py for the P1 data pipeline.

Rationale for a separate module:
  - The existing ECG SQI is tightly coupled to the backend's real-time path.
  - The P1 pipeline needs SQI on batches of windowed data.
  - This module provides the same SQI logic with a cleaner interface
    for manifest-level computation, configurable thresholds, and
    integration with WindowRecord objects.

Quality score: 0–100 (higher = better)
Quality states: EXCELLENT (≥80), GOOD (≥60), FAIR (≥40), POOR (<40)

Unit test signals covered:
  - Clean ECG (synthesize_ecg_segment)
  - Flatline
  - High-frequency noise
  - Baseline drift (0.2 Hz)
  - Clipped signal
  - Missing/NaN values
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np
from scipy import signal as scipy_signal

logger = logging.getLogger(__name__)


# ─── SQI Result ───────────────────────────────────────────────────────────────

@dataclass
class SQIResult:
    """
    Complete SQI result for a single ECG window.
    All component scores are in [0, 100].
    """
    overall_sqi: float              # Weighted composite: 0–100
    snr_score: float                # Signal-to-noise ratio component
    baseline_score: float           # Baseline stability component
    amplitude_score: float          # Amplitude range and consistency
    clipping_score: float           # Fraction of clipped samples
    flatline_score: float           # Absence of flatline

    quality_state: str              # EXCELLENT | GOOD | FAIR | POOR
    is_usable: bool                 # SQI above rejection threshold
    low_quality_reasons: List[str]  # Human-readable issues

    # Configurable thresholds used (stored for auditability)
    excellent_threshold: float = 80.0
    good_threshold: float = 60.0
    fair_threshold: float = 40.0
    reject_threshold: float = 20.0


# ─── SQI Calculator ───────────────────────────────────────────────────────────

class ECGQualityAssessor:
    """
    P1 ECG Signal Quality Index assessor.

    Computes a composite SQI score from multiple quality indicators.
    All indicators are deterministic and configurable.

    Parameters
    ----------
    excellent_threshold : float — SQI ≥ this → EXCELLENT
    good_threshold : float — SQI ≥ this → GOOD
    fair_threshold : float — SQI ≥ this → FAIR
    reject_threshold : float — SQI < this → unusable (reject window)
    flatline_std_threshold : float — signal std below this → flatline
    clipping_fraction_max : float — fraction of rail-clipped samples above this → penalty
    fs : int — expected sampling rate
    """

    def __init__(
        self,
        excellent_threshold: float = 80.0,
        good_threshold: float = 60.0,
        fair_threshold: float = 40.0,
        reject_threshold: float = 20.0,
        flatline_std_threshold: float = 0.002,
        clipping_fraction_max: float = 0.05,
        fs: int = 250,
    ):
        self.excellent_threshold = excellent_threshold
        self.good_threshold = good_threshold
        self.fair_threshold = fair_threshold
        self.reject_threshold = reject_threshold
        self.flatline_std_threshold = flatline_std_threshold
        self.clipping_fraction_max = clipping_fraction_max
        self.fs = fs

    # ── Component Scorers ─────────────────────────────────────────────────────

    def _snr_score(self, signal: np.ndarray) -> float:
        """
        SNR-based score.
        Estimate noise as deviation from a smoothed version of the signal.
        Score 0–100: higher = cleaner signal.
        """
        from scipy.signal import savgol_filter
        if len(signal) < 11:
            return 50.0
        try:
            smooth = savgol_filter(signal, window_length=11, polyorder=3)
        except Exception:
            smooth = np.ones_like(signal) * np.mean(signal)

        signal_power = np.var(smooth) + 1e-12
        noise_power = np.var(signal - smooth) + 1e-12
        snr_db = 10 * np.log10(signal_power / noise_power)
        # Map SNR in [5, 30] dB to [0, 100]
        return float(np.clip((snr_db - 5) / 25 * 100, 0, 100))

    def _baseline_score(self, signal: np.ndarray) -> float:
        """
        Baseline stability score.
        A high-energy low-frequency component indicates baseline drift.
        Score 0–100: higher = more stable baseline.
        """
        if len(signal) < 10:
            return 50.0
        try:
            b, a = scipy_signal.butter(2, 0.5 / (self.fs / 2), btype="low")
            lf = scipy_signal.filtfilt(b, a, signal)
            lf_ratio = np.var(lf) / (np.var(signal) + 1e-12)
            return float(np.clip(100 - lf_ratio * 200, 0, 100))
        except Exception:
            return 50.0

    def _amplitude_score(self, signal: np.ndarray) -> float:
        """
        Amplitude range score.
        Very low amplitude suggests poor electrode contact.
        Very high amplitude may indicate saturation.
        After z-score normalization, amplitude range should be roughly [−5, 5].
        Score 0–100.
        """
        amplitude_range = float(np.ptp(signal))  # peak-to-peak

        # After z-score normalization: range ~1–10 is normal
        if amplitude_range < 0.1:
            return 10.0  # Very low → poor contact
        if amplitude_range > 50.0:
            return 20.0  # Very high → saturation
        # Score peaks around range ~2–8 (typical z-scored ECG)
        score = 100 * (1 - abs(amplitude_range - 5) / 20)
        return float(np.clip(score, 10, 100))

    def _clipping_score(self, signal: np.ndarray) -> float:
        """
        Clipping/saturation score.
        Detects samples that are at the signal extremes (rail-clipped).
        Score 0–100: 100 = no clipping.
        """
        sig_max = np.max(np.abs(signal))
        if sig_max < 1e-6:
            return 100.0  # Flatline (handled by flatline score)

        threshold = 0.98 * sig_max
        clipped_fraction = float(np.mean(np.abs(signal) >= threshold))
        # Allow up to clipping_fraction_max before penalizing
        if clipped_fraction <= self.clipping_fraction_max:
            return 100.0
        penalty = (clipped_fraction - self.clipping_fraction_max) / 0.5 * 100
        return float(np.clip(100 - penalty, 0, 100))

    def _flatline_score(self, signal: np.ndarray) -> float:
        """
        Flatline detection score.
        Score 0 if signal is flat (std below threshold), 100 otherwise.
        """
        std = float(np.std(signal))
        if std < self.flatline_std_threshold:
            return 0.0
        # Gradual scoring: std in [0.002, 0.05] gets partial score
        if std < 0.05:
            score = (std - self.flatline_std_threshold) / 0.048 * 60
            return float(np.clip(score, 0, 60))
        return 100.0

    # ── Composite Score ───────────────────────────────────────────────────────

    def assess(self, signal: np.ndarray) -> SQIResult:
        """
        Compute composite SQI for a single ECG window.

        Weighted composite:
          0.30 × SNR
          0.25 × Baseline
          0.20 × Amplitude
          0.15 × Clipping
          0.10 × Flatline

        Parameters
        ----------
        signal : np.ndarray (1D, float32, already preprocessed)

        Returns
        -------
        SQIResult
        """
        if not np.isfinite(signal).all():
            return SQIResult(
                overall_sqi=0.0, snr_score=0.0, baseline_score=0.0,
                amplitude_score=0.0, clipping_score=0.0, flatline_score=0.0,
                quality_state="POOR", is_usable=False,
                low_quality_reasons=["NaN or Inf in signal"],
                excellent_threshold=self.excellent_threshold,
                good_threshold=self.good_threshold,
                fair_threshold=self.fair_threshold,
                reject_threshold=self.reject_threshold,
            )

        snr = self._snr_score(signal)
        baseline = self._baseline_score(signal)
        amplitude = self._amplitude_score(signal)
        clipping = self._clipping_score(signal)
        flatline = self._flatline_score(signal)

        # Flatline is a hard blocker — if flatline score is 0, overall is 0
        if flatline == 0.0:
            overall = 0.0
        else:
            overall = (
                0.30 * snr
                + 0.25 * baseline
                + 0.20 * amplitude
                + 0.15 * clipping
                + 0.10 * flatline
            )

        overall = float(np.clip(overall, 0, 100))

        # Quality state
        if overall >= self.excellent_threshold:
            state = "EXCELLENT"
        elif overall >= self.good_threshold:
            state = "GOOD"
        elif overall >= self.fair_threshold:
            state = "FAIR"
        else:
            state = "POOR"

        is_usable = overall >= self.reject_threshold

        reasons = []
        if snr < 40:
            reasons.append(f"Low SNR ({snr:.1f}/100)")
        if baseline < 40:
            reasons.append(f"Baseline drift ({baseline:.1f}/100)")
        if amplitude < 30:
            reasons.append(f"Low amplitude ({amplitude:.1f}/100)")
        if clipping < 60:
            reasons.append(f"Signal clipping ({clipping:.1f}/100)")
        if flatline < 50:
            reasons.append(f"Flatline detected ({flatline:.1f}/100)")

        return SQIResult(
            overall_sqi=round(overall, 2),
            snr_score=round(snr, 2),
            baseline_score=round(baseline, 2),
            amplitude_score=round(amplitude, 2),
            clipping_score=round(clipping, 2),
            flatline_score=round(flatline, 2),
            quality_state=state,
            is_usable=is_usable,
            low_quality_reasons=reasons,
            excellent_threshold=self.excellent_threshold,
            good_threshold=self.good_threshold,
            fair_threshold=self.fair_threshold,
            reject_threshold=self.reject_threshold,
        )

    def assess_batch(self, signals: list) -> List[SQIResult]:
        """Assess a list of signals. Returns list of SQIResult."""
        return [self.assess(s) for s in signals]

    def sqi_to_dict(self, result: SQIResult) -> dict:
        """Convert SQIResult to flat dict for DataFrame/logging."""
        return {
            "overall_sqi": result.overall_sqi,
            "snr_score": result.snr_score,
            "baseline_score": result.baseline_score,
            "amplitude_score": result.amplitude_score,
            "clipping_score": result.clipping_score,
            "flatline_score": result.flatline_score,
            "quality_state": result.quality_state,
            "is_usable": result.is_usable,
            "low_quality_reasons": "; ".join(result.low_quality_reasons),
        }
