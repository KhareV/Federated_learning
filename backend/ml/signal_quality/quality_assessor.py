from dataclasses import dataclass

@dataclass
class QualityAssessment:
    ecg_sqi: float
    ppg_sqi: float
    overall_sqi: float
    quality_label: str
    all_reasons: list
    is_reliable_for_ml: bool
    data_quality_score: float
    usable_sample_fraction: float

class QualityAssessor:
    def assess(self, ecg_result, ppg_result, ecg_sqi_result, ppg_sqi_result, missing_rate):
        overall = (ecg_sqi_result.overall_sqi * 0.6) + (ppg_sqi_result.overall_sqi * 0.4)
        return QualityAssessment(ecg_sqi_result.overall_sqi, ppg_sqi_result.overall_sqi, overall, 
                                 "GOOD", [], True, overall, 1.0)