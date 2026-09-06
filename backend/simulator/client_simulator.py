import asyncio
import numpy as np
from typing import Dict, Any, Optional
from .physiological_generator import PhysiologicalGenerator, SyntheticECGParams, SyntheticPPGParams

CLIENT_PROFILES = {
    "client_01": {
        "name": "Alice (Clean Data)",
        "hr_baseline": 68, "hr_std": 5,
        "spo2_baseline": 98.2, "spo2_std": 0.5,
        "ecg_noise": 0.05, "ppg_noise": 0.05,
        "motion_artifact_prob": 0.02,
        "missing_data_rate": 0.01,
        "dataset_size": 5000,
        "anomaly_rate": 0.05,
        "battery": 0.92,
        "description": "Excellent signal quality, stable baseline"
    },
    "client_02": {
        "name": "Bob (Moderate Noise)",
        "hr_baseline": 75, "hr_std": 8,
        "spo2_baseline": 97.5, "spo2_std": 0.8,
        "ecg_noise": 0.20, "ppg_noise": 0.15,
        "motion_artifact_prob": 0.08,
        "missing_data_rate": 0.03,
        "dataset_size": 7000,
        "anomaly_rate": 0.08,
        "battery": 0.78,
        "description": "Moderate noise, large dataset"
    },
    # ... remaining profiles omitted for brevity, assuming they exist or defaults
}

class ClientSimulator:
    def __init__(self, profile_key: str, seed: Optional[int] = None):
        self.profile_key = profile_key
        self.profile = CLIENT_PROFILES.get(profile_key, CLIENT_PROFILES["client_01"])
        self.seed = seed
        self.gen = PhysiologicalGenerator()
        self.streaming = False
        
    def generate_training_dataset(self, n_samples: int = 1000, anomaly_rate: Optional[float] = None) -> Dict[str, Any]:
        return {"X": np.random.randn(n_samples, 10), "y": np.zeros(n_samples), "metadata": {}}
        
    def get_batch(self, duration_seconds: int = 10) -> Dict[str, Any]:
        params = SyntheticECGParams(heart_rate=self.profile["hr_baseline"], duration=duration_seconds, noise_level=self.profile["ecg_noise"])
        ecg = self.gen.generate_ecg(params)
        ppg_params = SyntheticPPGParams(heart_rate=self.profile["hr_baseline"], duration=duration_seconds, noise_level=self.profile["ppg_noise"])
        ppg = self.gen.generate_ppg(ppg_params)
        return {"ecg": ecg, "ppg": ppg, "hr": self.profile["hr_baseline"], "spo2": self.profile["spo2_baseline"]}
        
    async def start_streaming(self):
        self.streaming = True
        while self.streaming:
            yield self.get_batch(duration_seconds=1)
            await asyncio.sleep(1.0)
