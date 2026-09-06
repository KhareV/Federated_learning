import numpy as np
from typing import List, Dict
from backend.federated.aggregation.quality_aggregator import ClientMetadata
from backend.federated.strategies.fedavg_strategy import FedAvgStrategy

class PersonalizedFLStrategy:
    def __init__(self, personalization_alpha: float = 0.3):
        self.fedavg = FedAvgStrategy()
        self.personalization_alpha = personalization_alpha
        self.strategy_name = "PersonalizedFL"
        self.personal_weights: Dict[str, Dict[str, np.ndarray]] = {}
    
    def compute_weights(self, clients: List[ClientMetadata]) -> Dict[str, float]:
        return self.fedavg.compute_weights(clients)
    
    def aggregate_weights(self, model_weights_list, client_weights) -> Dict[str, np.ndarray]:
        global_weights = self.fedavg.aggregate_weights(model_weights_list, client_weights)
        
        alpha = self.personalization_alpha
        client_ids = list(client_weights.keys())
        for i, client_id in enumerate(client_ids):
            personal = {}
            for param_name in global_weights.keys():
                personal[param_name] = (
                    (1 - alpha) * global_weights[param_name] + 
                    alpha * model_weights_list[i][param_name]
                )
            self.personal_weights[client_id] = personal
        
        return global_weights
    
    def get_personal_weights(self, client_id: str) -> Dict[str, np.ndarray]:
        return self.personal_weights.get(client_id, {})
