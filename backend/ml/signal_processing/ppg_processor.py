import numpy as np
from scipy import signal as sp_signal
from dataclasses import dataclass
from typing import Tuple

@dataclass
class PPGResult:
    filtered: np.ndarray
    peaks: np.ndarray
    pulse_intervals: np.ndarray
    amplitude: np.ndarray
    motion_artifact_detected: bool
    snr: float

class PPGProcessor:
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
        filtered = self.bandpass_filter(self.remove_dc(raw_ppg, fs=fs), fs=fs)
        peaks = self.detect_peaks(filtered, fs=fs)
        pulse_intervals = self.compute_pulse_intervals(peaks, fs)
        amplitude = self.estimate_pulse_amplitude(filtered, peaks)
        motion = self.detect_motion_artifact(raw_ppg, filtered, fs=fs)
        snr = self.compute_snr(raw_ppg, filtered)
        return PPGResult(filtered, peaks, pulse_intervals, amplitude, motion, snr)
