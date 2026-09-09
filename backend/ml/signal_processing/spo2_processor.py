from dataclasses import dataclass
import numpy as np

@dataclass
class SpO2Result:
    spo2: float
    smoothed: float
    confidence: float
    trend: float
    valid: bool = False
    quality_state: str = "UNRELIABLE"

class SpO2Processor:
    def process(self, spo2_series, timestamps=None):
        """Validate/smooth observed SpO2; never invent a reading."""
        values = np.asarray(spo2_series, dtype=float).flatten()
        finite = values[np.isfinite(values)]
        if len(finite) == 0:
            return SpO2Result(float("nan"), float("nan"), 0.0, 0.0, False, "UNRELIABLE")
        valid = finite[(finite >= 50.0) & (finite <= 100.0)]
        if len(valid) == 0:
            return SpO2Result(float("nan"), float("nan"), 0.0, 0.0, False, "UNRELIABLE")
        smoothed = float(np.median(valid[-min(5, len(valid)):]))
        confidence = float(min(1.0, len(valid) / 5.0))
        trend = float(valid[-1] - valid[0]) if len(valid) > 1 else 0.0
        state = "GOOD" if len(valid) >= 3 and confidence >= 0.6 else "DEGRADED"
        return SpO2Result(float(valid[-1]), smoothed, confidence, trend, True, state)
