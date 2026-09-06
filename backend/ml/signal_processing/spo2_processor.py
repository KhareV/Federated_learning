from dataclasses import dataclass

@dataclass
class SpO2Result:
    spo2: float
    smoothed: float
    confidence: float
    trend: float

class SpO2Processor:
    def process(self, spo2_series):
        return SpO2Result(98.0, 98.0, 1.0, 0.0)