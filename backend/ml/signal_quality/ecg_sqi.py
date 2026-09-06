import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ECGSQIResult:
    overall_sqi: float          # 0-100
    snr_score: float            # 0-100
    baseline_stability: float   # 0-100
    qrs_reliability: float      # 0-100
    amplitude_consistency: float # 0-100
    missing_data_penalty: float  # 0-100
    quality_label: str          # EXCELLENT/GOOD/FAIR/POOR
    low_quality_reasons: List[str] = field(default_factory=list)

class ECGSQICalculator:
    def snr_score(self, filtered_ecg, raw_ecg) -> float:
        signal_power = np.mean(filtered_ecg ** 2)
        noise = raw_ecg - filtered_ecg
        noise_power = np.mean(noise ** 2)
        if noise_power < 1e-12:
            return 100.0
        snr_db = 10 * np.log10(signal_power / (noise_power + 1e-12))
        return float(np.clip((snr_db - 5) / 25 * 100, 0, 100))
    
    def baseline_stability_score(self, ecg) -> float:
        from scipy import signal
        b, a = signal.butter(2, 0.5 / 125, btype='low')
        lf = signal.filtfilt(b, a, ecg)
        lf_power_ratio = np.var(lf) / (np.var(ecg) + 1e-12)
        return float(np.clip(100 - lf_power_ratio * 200, 0, 100))
    
    def qrs_reliability_score(self, r_peaks, rr_intervals) -> float:
        if len(rr_intervals) < 2:
            return 30.0
        cv = np.std(rr_intervals) / (np.mean(rr_intervals) + 1e-9)
        return float(np.clip(100 - cv * 200, 0, 100))
    
    def amplitude_consistency_score(self, r_peaks, ecg) -> float:
        if len(r_peaks) < 2:
            return 30.0
        amplitudes = ecg[r_peaks]
        if np.mean(amplitudes) < 1e-9:
            return 30.0
        cv = np.std(amplitudes) / (np.mean(np.abs(amplitudes)) + 1e-9)
        return float(np.clip(100 - cv * 150, 0, 100))
    
    def missing_data_score(self, missing_mask: Optional[np.ndarray]) -> float:
        if missing_mask is None:
            return 100.0
        missing_rate = np.mean(missing_mask)
        return float(np.clip(100 - missing_rate * 200, 0, 100))
    
    def compute_ecg_sqi(self, raw_ecg, filtered_ecg, r_peaks, rr_intervals, missing_mask=None) -> ECGSQIResult:
        snr = self.snr_score(filtered_ecg, raw_ecg)
        stability = self.baseline_stability_score(raw_ecg)
        reliability = self.qrs_reliability_score(r_peaks, rr_intervals)
        amplitude = self.amplitude_consistency_score(r_peaks, filtered_ecg)
        missing = self.missing_data_score(missing_mask)
        
        overall = (0.30 * snr + 0.20 * stability + 0.25 * reliability + 
                   0.15 * amplitude + 0.10 * missing)
        
        label = "EXCELLENT" if overall >= 80 else "GOOD" if overall >= 60 else "FAIR" if overall >= 40 else "POOR"
        
        reasons = []
        if snr < 50: reasons.append("Excessive signal noise")
        if stability < 50: reasons.append("Baseline drift/wander")
        if reliability < 50: reasons.append("Irregular QRS detection")
        if amplitude < 50: reasons.append("Inconsistent R-peak amplitude")
        if missing is not None and missing < 80: reasons.append("High missing data rate")
        
        return ECGSQIResult(
            overall_sqi=round(overall, 1),
            snr_score=round(snr, 1),
            baseline_stability=round(stability, 1),
            qrs_reliability=round(reliability, 1),
            amplitude_consistency=round(amplitude, 1),
            missing_data_penalty=round(missing, 1),
            quality_label=label,
            low_quality_reasons=reasons
        )
