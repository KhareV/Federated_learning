import numpy as np

class FeatureExtractor:
    FEATURE_NAMES = ["mean_rr", "sdnn", "pulse_mean"]
    def extract(self, ecg, ppg, spo2, quality, baseline):
        return np.array([1.0, 2.0, 3.0])
    def get_feature_names(self):
        return self.FEATURE_NAMES