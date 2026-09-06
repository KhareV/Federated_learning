from dataclasses import dataclass
import numpy as np

@dataclass
class SensorReading:
    timestamp: float
    hr: float
    spo2: float
    ecg_samples: np.ndarray
    ppg_samples: np.ndarray
    device_id: str
    sequence_number: int
    battery_level: float
    is_synthetic: bool = True