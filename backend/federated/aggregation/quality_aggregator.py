import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

@dataclass
class ClientMetadata:
    client_id: str
    profile: dict
    dataset_size: int
    usable_samples: int
    ecg_sqi: float          # 0-100
    ppg_sqi: float          # 0-100
    local_accuracy: float   # 0-1
    local_f1: float         # 0-1
    local_loss: float       # positive float
    uncertainty: float      # 0-1 (from MC Dropout)
    battery_level: float    # 0-1
    last_participation: float  # Unix timestamp
    aggregation_weight: float = 0.0

@dataclass
class AggregationAudit:
    client_scores: Dict[str, float] = field(default_factory=dict)
    client_weights: Dict[str, float] = field(default_factory=dict)
    client_reasoning: Dict[str, str] = field(default_factory=dict)
    component_scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strategy: str = "QAPFL"
    alpha: float = 0.0
    beta: float = 0.0
    gamma: float = 0.0
    delta: float = 0.0

class QualityAwareAggregator:
    def __init__(self):
        self.alpha = settings.qapfl_alpha
        self.beta = settings.qapfl_beta
        self.gamma = settings.qapfl_gamma
        self.delta = settings.qapfl_delta
        
        total = self.alpha + self.beta + self.gamma + self.delta
        if abs(total - 1.0) > 0.01:
            logger.warning(f"QAPFL weights sum to {total:.3f} (should be 1.0). Normalizing.")
            self.alpha /= total
            self.beta /= total
            self.gamma /= total
            self.delta /= total
    
    def _compute_components(self, meta: ClientMetadata) -> Dict[str, float]:
        q_signal = (meta.ecg_sqi + meta.ppg_sqi) / 2.0 / 100.0
        q_data = meta.usable_samples / max(1, meta.dataset_size)
        q_model = meta.local_f1
        q_uncert = 1.0 - meta.uncertainty
        
        return {
            "signal_quality": float(np.clip(q_signal, 0, 1)),
            "data_quality": float(np.clip(q_data, 0, 1)),
            "model_performance": float(np.clip(q_model, 0, 1)),
            "uncertainty_reliability": float(np.clip(q_uncert, 0, 1)),
        }
    
    def compute_quality_score(self, meta: ClientMetadata) -> float:
        c = self._compute_components(meta)
        score = (self.alpha * c["signal_quality"] +
                 self.beta * c["data_quality"] +
                 self.gamma * c["model_performance"] +
                 self.delta * c["uncertainty_reliability"])
        return float(score)
    
    def compute_weights(self, clients: List[ClientMetadata]) -> Dict[str, float]:
        scores = np.array([self.compute_quality_score(c) for c in clients])
        exp_scores = np.exp(scores - np.max(scores))
        weights = exp_scores / np.sum(exp_scores)
        return {c.client_id: float(w) for c, w in zip(clients, weights)}
    
    def aggregate_weights(self, model_weights_list: List[Dict[str, np.ndarray]], client_weights: Dict[str, float]) -> Dict[str, np.ndarray]:
        if not model_weights_list:
            raise ValueError("No model weights provided for aggregation")
        
        weight_values = list(client_weights.values())
        aggregated = {}
        
        for param_name in model_weights_list[0].keys():
            weighted_sum = np.zeros_like(model_weights_list[0][param_name], dtype=np.float64)
            for w, client_model in zip(weight_values, model_weights_list):
                weighted_sum += w * client_model[param_name].astype(np.float64)
            aggregated[param_name] = weighted_sum.astype(np.float32)
        
        return aggregated
    
    def get_reasoning(self, client_id: str, meta: ClientMetadata, weight: float) -> str:
        c = self._compute_components(meta)
        score = self.compute_quality_score(meta)
        
        parts = []
        sqi_avg = (meta.ecg_sqi + meta.ppg_sqi) / 2
        if sqi_avg >= 80: parts.append(f"Excellent signal quality (ECG SQI: {meta.ecg_sqi:.0f}%, PPG SQI: {meta.ppg_sqi:.0f}%)")
        elif sqi_avg >= 60: parts.append(f"Good signal quality (ECG SQI: {meta.ecg_sqi:.0f}%, PPG SQI: {meta.ppg_sqi:.0f}%)")
        elif sqi_avg >= 40: parts.append(f"Fair signal quality — reduced contribution")
        else: parts.append(f"Poor signal quality — significantly reduced contribution")
        
        data_util = meta.usable_samples / max(1, meta.dataset_size)
        if data_util < 0.7: parts.append(f"High missing/unusable data rate")
        
        if meta.local_f1 >= 0.85: parts.append(f"High local model F1 ({meta.local_f1:.3f})")
        elif meta.local_f1 < 0.6: parts.append(f"Low local model F1 ({meta.local_f1:.3f})")
        
        if meta.uncertainty > 0.4: parts.append(f"High prediction uncertainty ({meta.uncertainty:.2f})")
        
        return f"QAPFL weight: {weight:.4f} (raw score: {score:.4f}). " + "; ".join(parts) + "."
    
    def full_audit(self, clients: List[ClientMetadata]) -> AggregationAudit:
        weights = self.compute_weights(clients)
        audit = AggregationAudit(strategy="QAPFL", alpha=self.alpha, beta=self.beta, gamma=self.gamma, delta=self.delta)
        for meta in clients:
            cid = meta.client_id
            score = self.compute_quality_score(meta)
            audit.client_scores[cid] = score
            audit.client_weights[cid] = weights[cid]
            audit.client_reasoning[cid] = self.get_reasoning(cid, meta, weights[cid])
            audit.component_scores[cid] = self._compute_components(meta)
        return audit
