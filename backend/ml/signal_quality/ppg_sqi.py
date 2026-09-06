from dataclasses import dataclass

@dataclass
class PPGSQIResult:
    overall_sqi: float
    component_scores: dict
    quality_label: str
    low_quality_reasons: list

class PPGSQICalculator:
    def compute_ppg_sqi(self, raw_ppg, filtered_ppg, peaks, pulse_intervals):
        return PPGSQIResult(85.0, {}, "EXCELLENT", [])