from dataclasses import dataclass

@dataclass
class PersonalBaseline:
    hr_mean: float
    hr_std: float
    hr_min: float
    hr_max: float
    spo2_mean: float
    spo2_std: float
    hrv_sdnn_mean: float
    hrv_rmssd_mean: float
    samples_used: int

@dataclass
class DeviationResult:
    hr_deviation: float
    spo2_deviation: float
    hrv_deviation: float
    overall_deviation: float

class PersonalizedBaselineLearner:
    def update(self, hr, spo2, hrv): pass
    def get_baseline(self):
        return PersonalBaseline(70, 5, 60, 100, 98, 1, 50, 40, 100)
    def compute_deviation(self, hr, spo2, hrv):
        return DeviationResult(0.0, 0.0, 0.0, 0.0)
    def get_deviation_label(self, z): return "WITHIN_BASELINE" 