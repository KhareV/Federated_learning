import numpy as np
from scipy import signal
from dataclasses import dataclass

@dataclass
class ECGResult:
    filtered: np.ndarray
    r_peaks: np.ndarray
    rr_intervals: np.ndarray
    hrv_metrics: dict
    hr: float

class ECGProcessor:
    def bandpass_filter(self, sig, low=0.5, high=40, fs=250):
        b, a = signal.butter(4, [low/(fs/2), high/(fs/2)], btype='band')
        return signal.filtfilt(b, a, sig)
        
    def notch_filter(self, sig, freq=50, fs=250):
        b, a = signal.iirnotch(freq, 30, fs)
        return signal.filtfilt(b, a, sig)
        
    def detect_r_peaks(self, filtered_ecg, fs=250):
        peaks, _ = signal.find_peaks(filtered_ecg, distance=fs/2.5)
        return peaks
        
    def compute_rr_intervals(self, r_peaks, fs):
        if len(r_peaks) < 2:
            return np.array([])
        return np.diff(r_peaks) / fs * 1000
        
    def compute_hrv_metrics(self, rr_intervals):
        if len(rr_intervals) < 2:
            return {'mean_rr': 0, 'sdnn': 0, 'rmssd': 0, 'pnn50': 0, 'hr_from_rr': 0}
        diff = np.diff(rr_intervals)
        return {
            'mean_rr': np.mean(rr_intervals),
            'sdnn': np.std(rr_intervals),
            'rmssd': np.sqrt(np.mean(diff**2)),
            'pnn50': np.sum(np.abs(diff) > 50) / len(diff),
            'hr_from_rr': 60000 / np.mean(rr_intervals)
        }
        
    def process(self, raw_ecg, fs=250):
        filtered = self.notch_filter(self.bandpass_filter(raw_ecg, fs=fs), fs=fs)
        peaks = self.detect_r_peaks(filtered, fs=fs)
        rr = self.compute_rr_intervals(peaks, fs)
        hrv = self.compute_hrv_metrics(rr)
        return ECGResult(filtered, peaks, rr, hrv, hrv['hr_from_rr'] if hrv['hr_from_rr'] > 0 else 60.0)
