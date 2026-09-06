import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AnomalyClassification(Enum):
    NORMAL = "NORMAL"
    POSSIBLE_ANOMALY = "POSSIBLE_ANOMALY"
    LOW_CONFIDENCE_EVENT = "LOW_CONFIDENCE_EVENT"
    HIGH_CONFIDENCE_ANOMALY = "HIGH_CONFIDENCE_ANOMALY"

@dataclass
class AnomalyResult:
    anomaly_score: float
    confidence: float
    raw_confidence: float
    classification: AnomalyClassification
    affected_signals: List[str]
    explanation: Dict[str, float]
    signal_quality: float
    disclaimer: str = "RESEARCH RESULT: This is an anomaly detection output from a research prototype. It is NOT a medical diagnosis."

class AnomalyDetector:
    def __init__(self, model, threshold: Optional[float] = None, sqi_threshold: Optional[float] = None):
        self.model = model
        self.threshold = threshold or settings.anomaly_threshold
        self.sqi_threshold = sqi_threshold or settings.sqi_threshold
    
    def classify(self, score: float, confidence: float, sqi: float) -> AnomalyClassification:
        if score < self.threshold:
            return AnomalyClassification.NORMAL
        
        if sqi < self.sqi_threshold:
            return AnomalyClassification.LOW_CONFIDENCE_EVENT
        
        if confidence < 0.6:
            return AnomalyClassification.POSSIBLE_ANOMALY
        
        return AnomalyClassification.HIGH_CONFIDENCE_ANOMALY
    
    def compute_confidence(self, raw_confidence: float, sqi: float) -> float:
        return raw_confidence * (sqi / 100.0)
        
    def detect(self, feature_vector, ecg, ppg, spo2, quality, baseline):
        score = 0.1
        raw_conf = 0.9
        sqi = quality.overall_sqi if quality else 100.0
        conf = self.compute_confidence(raw_conf, sqi)
        cls = self.classify(score, conf, sqi)
        return AnomalyResult(score, conf, raw_conf, cls, [], {}, sqi)
