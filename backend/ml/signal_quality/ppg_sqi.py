from dataclasses import dataclass
import numpy as np

@dataclass
class PPGSQIResult:
    overall_sqi: float
    component_scores: dict
    quality_label: str
    low_quality_reasons: list

class PPGSQICalculator:
    def compute_ppg_sqi(self, raw_ppg, filtered_ppg, peaks, pulse_intervals):
        raw_ppg = np.asarray(raw_ppg, dtype=float)
        filtered_ppg = np.asarray(filtered_ppg, dtype=float)
        if len(raw_ppg) == 0 or not np.isfinite(raw_ppg).all() or not np.isfinite(filtered_ppg).all():
            return PPGSQIResult(0.0, {"finite": 0.0}, "UNRELIABLE", ["missing or non-finite samples"])
        signal_power = float(np.var(filtered_ppg))
        noise_power = float(np.var(raw_ppg - filtered_ppg))
        snr = 100.0 if noise_power < 1e-12 else float(np.clip((10 * np.log10((signal_power + 1e-12) / noise_power) + 5) / 25 * 100, 0, 100))
        interval_score = 100.0
        reasons = []
        if len(pulse_intervals) < 2:
            interval_score = 20.0
            reasons.append("insufficient pulse detections")
        elif np.mean(pulse_intervals) <= 0 or np.std(pulse_intervals) / np.mean(pulse_intervals) > 0.2:
            interval_score = 40.0
            reasons.append("unstable pulse intervals")
        amplitude = float(np.clip(100.0 * np.std(filtered_ppg) / (np.std(raw_ppg) + 1e-8), 0, 100))
        overall = float(np.clip(0.5 * snr + 0.3 * interval_score + 0.2 * amplitude, 0, 100))
        state = "GOOD" if overall >= 60 else "DEGRADED" if overall >= 30 else "UNRELIABLE"
        if state == "UNRELIABLE":
            reasons.append("low composite PPG quality")
        return PPGSQIResult(round(overall, 2), {"snr": round(snr, 2), "pulse": interval_score, "amplitude": round(amplitude, 2)}, state, reasons)
