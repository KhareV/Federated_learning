import numpy as np
from scipy import signal as sp_signal
from dataclasses import dataclass
from typing import Tuple, Dict

@dataclass
class PPGResult:
    filtered: np.ndarray
    peaks: np.ndarray
    pulse_intervals: np.ndarray
    amplitude: np.ndarray
    motion_artifact_detected: bool
    snr: float
    heart_rate_bpm: float = 0.0
    quality_state: str = "UNRELIABLE"
    feature_values: Dict[str, float] = None

    def __post_init__(self):
        if self.feature_values is None:
            self.feature_values = {}

class PPGProcessor:
    @staticmethod
    def _validate_and_interpolate(sig):
        """Preserve missingness semantics while repairing sparse NaNs safely."""
        values = np.asarray(sig, dtype=np.float32).flatten()
        if len(values) == 0:
            return values, "empty"
        finite = np.isfinite(values)
        if finite.mean() < 0.8:
            return values, "excessive_nonfinite"
        if finite.sum() < 2 or np.var(values[finite]) < 1e-7:
            return values, "flatline"
        if finite.all():
            return values, None
        indexes = np.arange(len(values))
        repaired = values.copy()
        repaired[~finite] = np.interp(indexes[~finite], indexes[finite], values[finite])
        return repaired, None

    def remove_dc(self, sig, fs=50):
        b, a = sp_signal.butter(2, 0.5/(fs/2), btype='high')
        return sp_signal.filtfilt(b, a, sig)
    
    def bandpass_filter(self, sig, low=0.5, high=5.0, fs=50):
        nyq = fs / 2.0
        b, a = sp_signal.butter(4, [low/nyq, high/nyq], btype='band')
        return sp_signal.filtfilt(b, a, sig)
    
    def detect_peaks(self, filtered_ppg, fs=50):
        min_distance = int(0.4 * fs)
        prominence = 0.05 * (np.max(filtered_ppg) - np.min(filtered_ppg))
        peaks, props = sp_signal.find_peaks(filtered_ppg, distance=min_distance, prominence=prominence)
        return peaks
    
    def compute_pulse_intervals(self, peaks, fs):
        if len(peaks) < 2:
            return np.array([])
        return np.diff(peaks) / fs * 1000  # ms
    
    def estimate_pulse_amplitude(self, filtered_ppg, peaks):
        if len(peaks) == 0:
            return np.array([])
        return filtered_ppg[peaks]
    
    def detect_motion_artifact(self, raw_ppg, filtered_ppg, fs=50):
        residual = raw_ppg - filtered_ppg
        signal_power = np.mean(filtered_ppg ** 2)
        artifact_power = np.mean(residual ** 2)
        snr = signal_power / (artifact_power + 1e-9)
        return snr < 5.0  # Threshold: SNR below 5 suggests motion artifact
    
    def compute_snr(self, raw_ppg, filtered_ppg):
        signal_power = np.mean(filtered_ppg ** 2)
        noise_power = np.mean((raw_ppg - filtered_ppg) ** 2)
        if noise_power < 1e-12:
            return 40.0
        return 10 * np.log10(signal_power / noise_power)
    
    def process(self, raw_ppg, fs=50):
        raw_ppg = np.asarray(raw_ppg, dtype=np.float32).flatten()
        if len(raw_ppg) < max(20, int(fs * 2)):
            return PPGResult(raw_ppg, np.array([], dtype=int), np.array([]), np.array([]), True, 0.0)
        raw_ppg, invalid_reason = self._validate_and_interpolate(raw_ppg)
        if invalid_reason is not None:
            return PPGResult(raw_ppg, np.array([], dtype=int), np.array([]), np.array([]), True, 0.0,
                             0.0, "UNRELIABLE", {"reason": invalid_reason})
        filtered = self.bandpass_filter(self.remove_dc(raw_ppg, fs=fs), fs=fs)
        peaks = self.detect_peaks(filtered, fs=fs)
        pulse_intervals = self.compute_pulse_intervals(peaks, fs)
        amplitude = self.estimate_pulse_amplitude(filtered, peaks)
        motion = self.detect_motion_artifact(raw_ppg, filtered, fs=fs)
        snr = self.compute_snr(raw_ppg, filtered)
        heart_rate = float(60000.0 / np.median(pulse_intervals)) if len(pulse_intervals) else 0.0
        if motion or len(peaks) < 2 or not np.isfinite(snr):
            state = "UNRELIABLE"
        elif snr < 5.0 or len(pulse_intervals) < 3:
            state = "DEGRADED"
        else:
            state = "GOOD"
        features = {
            "heart_rate_bpm": heart_rate,
            "pulse_interval_ms": float(np.median(pulse_intervals)) if len(pulse_intervals) else 0.0,
            "pulse_amplitude_median": float(np.median(np.abs(amplitude))) if len(amplitude) else 0.0,
        }
        return PPGResult(filtered, peaks, pulse_intervals, amplitude, motion, snr, heart_rate, state, features)
