import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from backend.federated.aggregation.quality_aggregator import ClientMetadata

@dataclass
class RoundResult:
    round_number: int
    strategy: str
    participating_client_ids: List[str]
    avg_local_loss: float
    avg_local_accuracy: float
    avg_local_f1: float
    global_accuracy: float
    global_f1: float
    global_loss: float
    avg_sqi: float
    communication_cost_bytes: int
    training_time_seconds: float
    aggregation_weights: Dict[str, float]
    aggregation_reasoning: Optional[Dict[str, str]] = None

class FedAvgStrategy:
    def __init__(self, weighted_by_dataset_size: bool = True):
        self.weighted_by_dataset_size = weighted_by_dataset_size
        self.strategy_name = "FedAvg"
    
    def compute_weights(self, clients: List[ClientMetadata]) -> Dict[str, float]:
        if not clients: return {}
        if self.weighted_by_dataset_size:
            total = sum(c.usable_samples for c in clients)
            if total == 0:
                total = len(clients)
                return {c.client_id: 1.0 / len(clients) for c in clients}
            return {c.client_id: c.usable_samples / total for c in clients}
        else:
            n = len(clients)
            return {c.client_id: 1.0 / n for c in clients}
    
    def aggregate_weights(self, model_weights_list: List[Dict[str, np.ndarray]], client_weights: Dict[str, float]) -> Dict[str, np.ndarray]:
        if not model_weights_list: raise ValueError("No model weights provided")
        weight_values = list(client_weights.values())
        aggregated = {}
        for param_name in model_weights_list[0].keys():
            weighted_sum = np.zeros_like(model_weights_list[0][param_name], dtype=np.float64)
            for w, client_model in zip(weight_values, model_weights_list):
                weighted_sum += w * client_model[param_name].astype(np.float64)
            aggregated[param_name] = weighted_sum.astype(np.float32)
        return aggregated
