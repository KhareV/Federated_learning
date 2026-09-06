"""
features/ecg_features.py — Deterministic ECG Feature Library
=============================================================
Provides reliable, explainable features for classical ML models.

All features:
  - Are deterministic (same input → same output)
  - Handle bad input (NaN, short signals) without raising exceptions
  - Return finite float values or explicit sentinel (NaN for missing)
  - Are documented with units and meaning
  - Have unit tests in tests/test_features.py

Feature groups:
  1. TIME_DOMAIN — statistics over the raw signal amplitude
  2. HRV — heart rate variability from R-peaks
  3. MORPHOLOGY — waveform shape descriptors
  4. SPECTRAL — frequency-domain characteristics
  5. QUALITY — SQI components as features (signal reliability)

Feature vector has fixed length: len(ECGFeatureExtractor.FEATURE_NAMES).
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

import numpy as np
from scipy import signal as scipy_signal
from scipy.stats import skew, kurtosis

logger = logging.getLogger(__name__)

FEATURE_VERSION = "1.0.0"


@dataclass
class ECGFeatureSet:
    """Container for computed ECG features with names and values."""
    feature_names: List[str]
    feature_values: np.ndarray     # (n_features,) float32
    feature_version: str = FEATURE_VERSION
    record_id: str = "unknown"
    is_valid: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, float]:
        return dict(zip(self.feature_names, self.feature_values.tolist()))


class ECGFeatureExtractor:
    """
    Deterministic ECG feature extractor for the P1 pipeline.

    Uses a preprocessed ECG window (float32, 1D) as input.
    Returns a fixed-length feature vector and named feature set.

    Parameters
    ----------
    fs : int — sampling rate (Hz), expected 250
    """

    def __init__(self, fs: int = 250):
        self.fs = fs
        self._feature_version = FEATURE_VERSION

    # ── Feature Names (must match extraction order) ───────────────────────────

    @property
    def FEATURE_NAMES(self) -> List[str]:
        """
        Ordered list of all feature names.
        Any change here requires incrementing FEATURE_VERSION.
        """
        return [
            # --- Time domain (10 features) ---
            "td_mean",
            "td_std",
            "td_var",
            "td_rms",
            "td_min",
            "td_max",
            "td_range",
            "td_p10",
            "td_p25",
            "td_p75",
            "td_p90",
            "td_iqr",
            "td_skewness",
            "td_kurtosis",
            "td_zero_crossing_rate",
            # --- HRV features (8 features) ---
            "hrv_n_rpeaks",
            "hrv_mean_rr_ms",
            "hrv_std_rr_ms",       # SDNN
            "hrv_rmssd_ms",
            "hrv_pnn50",
            "hrv_mean_hr_bpm",
            "hrv_hr_range_bpm",
            "hrv_rr_cv",           # Coefficient of variation
            # --- Morphology (6 features) ---
            "morph_rpeak_mean_amp",
            "morph_rpeak_std_amp",
            "morph_rpeak_cv",
            "morph_qrs_width_mean_ms",
            "morph_wave_symmetry",
            "morph_envelope_std",
            # --- Spectral (8 features) ---
            "spec_vlf_power",      # <0.04 Hz
            "spec_lf_power",       # 0.04–0.15 Hz
            "spec_hf_power",       # 0.15–0.40 Hz
            "spec_lf_hf_ratio",
            "spec_total_power",
            "spec_dominant_freq",
            "spec_spectral_entropy",
            "spec_spectral_edge_95",
            # --- Quality as features (5 features) ---
            "qual_sqi_overall",
            "qual_snr_proxy",
            "qual_flatline_flag",
            "qual_clipping_fraction",
            "qual_missing_fraction",
        ]

    @property
    def n_features(self) -> int:
        return len(self.FEATURE_NAMES)

    # ── Main Extraction Entry Point ───────────────────────────────────────────

    def extract(
        self,
        signal: np.ndarray,
        record_id: str = "unknown",
        sqi_overall: float = -1.0,
    ) -> ECGFeatureSet:
        """
        Extract all features from a preprocessed ECG window.

        Parameters
        ----------
        signal : np.ndarray (1D float32, preprocessed)
        record_id : str — for logging
        sqi_overall : float — overall SQI score (if already computed)

        Returns
        -------
        ECGFeatureSet
        """
        values = np.full(self.n_features, np.nan, dtype=np.float32)
        notes = []

        if len(signal) == 0 or not np.isfinite(signal).all():
            return ECGFeatureSet(
                feature_names=self.FEATURE_NAMES,
                feature_values=values,
                record_id=record_id,
                is_valid=False,
                notes="Empty or non-finite signal",
            )

        idx = 0
        # ── Time domain ──────────────────────────────────────────────────────
        td = self._time_domain(signal)
        for v in td:
            values[idx] = v
            idx += 1

        # ── HRV ──────────────────────────────────────────────────────────────
        hrv = self._hrv_features(signal)
        for v in hrv:
            values[idx] = v
            idx += 1

        # ── Morphology ───────────────────────────────────────────────────────
        morph = self._morphology_features(signal)
        for v in morph:
            values[idx] = v
            idx += 1

        # ── Spectral ─────────────────────────────────────────────────────────
        spec = self._spectral_features(signal)
        for v in spec:
            values[idx] = v
            idx += 1

        # ── Quality-as-features ───────────────────────────────────────────────
        qual = self._quality_features(signal, sqi_overall)
        for v in qual:
            values[idx] = v
            idx += 1

        # Replace any remaining NaN with 0 for robust sklearn compatibility
        values = np.where(np.isfinite(values), values, 0.0).astype(np.float32)

        return ECGFeatureSet(
            feature_names=self.FEATURE_NAMES,
            feature_values=values,
            feature_version=self._feature_version,
            record_id=record_id,
            is_valid=True,
        )

    def extract_batch(
        self,
        signals: List[np.ndarray],
        record_ids: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Extract features for a batch of signals.

        Returns
        -------
        np.ndarray, shape (n_signals, n_features)
        """
        if record_ids is None:
            record_ids = [f"signal_{i}" for i in range(len(signals))]

        rows = []
        for sig, rid in zip(signals, record_ids):
            fs = self.extract(sig, record_id=rid)
            rows.append(fs.feature_values)
        return np.stack(rows, axis=0)

    # ── Time Domain Features ──────────────────────────────────────────────────

    def _time_domain(self, signal: np.ndarray) -> List[float]:
        """
        15 time-domain statistical features.
        All computed on the raw amplitude of the preprocessed signal.
        """
        s = signal.astype(np.float64)
        mean = float(np.mean(s))
        std = float(np.std(s))
        var = float(np.var(s))
        rms = float(np.sqrt(np.mean(s ** 2)))
        mn = float(np.min(s))
        mx = float(np.max(s))
        rng = mx - mn
        p10 = float(np.percentile(s, 10))
        p25 = float(np.percentile(s, 25))
        p75 = float(np.percentile(s, 75))
        p90 = float(np.percentile(s, 90))
        iqr = p75 - p25

        try:
            sk = float(skew(s))
        except Exception:
            sk = 0.0
        try:
            kurt = float(kurtosis(s))
        except Exception:
            kurt = 0.0

        # Zero-crossing rate (normalized by signal length)
        zcr = float(np.sum(np.diff(np.sign(s)) != 0) / len(s))

        return [mean, std, var, rms, mn, mx, rng, p10, p25, p75, p90, iqr,
                sk, kurt, zcr]

    # ── HRV Features ─────────────────────────────────────────────────────────

    def _hrv_features(self, signal: np.ndarray) -> List[float]:
        """
        8 HRV-related features from R-peak detection.
        Returns sentinel values (0.0) if insufficient beats detected.
        """
        sentinel = [0.0] * 8
        try:
            peaks, _ = scipy_signal.find_peaks(
                signal, distance=int(self.fs * 0.4),
                height=float(np.mean(signal) + 0.3 * np.std(signal))
            )

            n_peaks = len(peaks)
            if n_peaks < 2:
                return [float(n_peaks)] + [0.0] * 7

            rr_samples = np.diff(peaks)
            rr_ms = rr_samples / self.fs * 1000.0

            mean_rr = float(np.mean(rr_ms))
            std_rr = float(np.std(rr_ms))
            rmssd = float(np.sqrt(np.mean(np.diff(rr_ms) ** 2))) if len(rr_ms) > 1 else 0.0
            pnn50 = float(np.mean(np.abs(np.diff(rr_ms)) > 50)) if len(rr_ms) > 1 else 0.0
            mean_hr = 60000.0 / mean_rr if mean_rr > 0 else 0.0
            hr_values = 60000.0 / rr_ms
            hr_range = float(np.ptp(hr_values)) if len(hr_values) > 1 else 0.0
            rr_cv = std_rr / (mean_rr + 1e-9)

            return [float(n_peaks), mean_rr, std_rr, rmssd, pnn50,
                    mean_hr, hr_range, rr_cv]

        except Exception as exc:
            logger.debug(f"HRV extraction failed: {exc}")
            return sentinel

    # ── Morphology Features ───────────────────────────────────────────────────

    def _morphology_features(self, signal: np.ndarray) -> List[float]:
        """
        6 waveform morphology features.
        """
        sentinel = [0.0] * 6
        try:
            peaks, _ = scipy_signal.find_peaks(
                signal, distance=int(self.fs * 0.4),
                height=float(np.mean(signal))
            )

            if len(peaks) < 2:
                return sentinel

            amplitudes = signal[peaks].astype(np.float64)
            mean_amp = float(np.mean(amplitudes))
            std_amp = float(np.std(amplitudes))
            cv = std_amp / (abs(mean_amp) + 1e-9)

            # Estimate QRS width: samples between threshold crossings around peaks
            qrs_widths = []
            threshold = mean_amp * 0.5
            for peak in peaks:
                window = 20  # ±80ms at 250 Hz
                l = max(0, peak - window)
                r = min(len(signal), peak + window)
                seg = signal[l:r]
                above = np.where(seg > threshold)[0]
                if len(above) > 1:
                    qrs_widths.append((above[-1] - above[0]) / self.fs * 1000)
            qrs_width_mean = float(np.mean(qrs_widths)) if qrs_widths else 0.0

            # Wave symmetry: correlation between pre- and post-R window
            sym_values = []
            half = int(self.fs * 0.08)  # 80ms window
            for peak in peaks:
                pre = signal[max(0, peak - half):peak]
                post = signal[peak:min(len(signal), peak + half)]
                if len(pre) > 5 and len(post) > 5:
                    min_len = min(len(pre), len(post))
                    pre = pre[-min_len:]
                    post = post[:min_len]
                    try:
                        corr = float(np.corrcoef(pre, post[::-1])[0, 1])
                        if np.isfinite(corr):
                            sym_values.append(corr)
                    except Exception:
                        pass
            wave_sym = float(np.mean(sym_values)) if sym_values else 0.0

            # Envelope standard deviation (Hilbert transform)
            try:
                analytic = scipy_signal.hilbert(signal)
                envelope = np.abs(analytic)
                env_std = float(np.std(envelope))
            except Exception:
                env_std = float(np.std(signal))

            return [mean_amp, std_amp, cv, qrs_width_mean, wave_sym, env_std]

        except Exception as exc:
            logger.debug(f"Morphology extraction failed: {exc}")
            return sentinel

    # ── Spectral Features ─────────────────────────────────────────────────────

    def _spectral_features(self, signal: np.ndarray) -> List[float]:
        """
        8 frequency-domain features using Welch's PSD estimate.

        Frequency bands:
          VLF: <0.04 Hz (respiratory/thermoregulatory)
          LF:  0.04–0.15 Hz (sympathetic + parasympathetic HRV)
          HF:  0.15–0.40 Hz (parasympathetic HRV, respiratory)
        """
        sentinel = [0.0] * 8
        try:
            # Welch PSD
            nperseg = min(len(signal), 512)
            freqs, psd = scipy_signal.welch(
                signal, fs=self.fs, nperseg=nperseg, scaling="density"
            )

            def band_power(flo, fhi):
                mask = (freqs >= flo) & (freqs < fhi)
                if not mask.any():
                    return 0.0
                return float(np.trapz(psd[mask], freqs[mask]))

            vlf = band_power(0.0, 0.04)
            lf = band_power(0.04, 0.15)
            hf = band_power(0.15, 0.40)
            total = band_power(0.0, self.fs / 2)
            lf_hf = lf / (hf + 1e-9)
            dom_freq = float(freqs[np.argmax(psd)])

            # Spectral entropy
            psd_norm = psd / (np.sum(psd) + 1e-12)
            spec_ent = float(-np.sum(psd_norm * np.log2(psd_norm + 1e-12)))

            # Spectral edge frequency (95% of power below this freq)
            cumulative = np.cumsum(psd)
            cumulative /= cumulative[-1] + 1e-12
            edge_idx = np.searchsorted(cumulative, 0.95)
            edge_freq = float(freqs[min(edge_idx, len(freqs) - 1)])

            return [vlf, lf, hf, lf_hf, total, dom_freq, spec_ent, edge_freq]

        except Exception as exc:
            logger.debug(f"Spectral extraction failed: {exc}")
            return sentinel

    # ── Quality-as-Features ────────────────────────────────────────────────────

    def _quality_features(
        self, signal: np.ndarray, sqi_overall: float = -1.0
    ) -> List[float]:
        """
        5 quality-related features.
        These are included in the feature vector so classical models can
        learn to weight predictions by signal reliability.
        """
        # SQI overall (if provided externally)
        sqi = sqi_overall if sqi_overall >= 0 else 50.0

        # SNR proxy: ratio of signal variance to high-freq noise variance
        try:
            b, a = scipy_signal.butter(
                2, [1.0 / (self.fs / 2), 40.0 / (self.fs / 2)], btype="band"
            )
            filtered = scipy_signal.filtfilt(b, a, signal)
            noise = signal - filtered
            snr_proxy = float(
                np.var(filtered) / (np.var(noise) + 1e-12)
            )
            snr_proxy = float(np.clip(np.log10(snr_proxy + 1e-6), -3, 5))
        except Exception:
            snr_proxy = 0.0

        # Flatline flag
        flatline_flag = 1.0 if float(np.std(signal)) < 0.002 else 0.0

        # Clipping fraction
        sig_max = np.max(np.abs(signal))
        if sig_max > 1e-6:
            clip_frac = float(np.mean(np.abs(signal) >= 0.98 * sig_max))
        else:
            clip_frac = 0.0

        # Missing fraction (NaN would have been zeroed by preprocessor)
        missing_frac = 0.0  # After preprocessing, NaNs are replaced

        return [sqi, snr_proxy, flatline_flag, clip_frac, missing_frac]
