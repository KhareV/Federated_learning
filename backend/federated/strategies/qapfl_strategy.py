import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from backend.federated.aggregation.quality_aggregator import QualityAwareAggregator, ClientMetadata, AggregationAudit
from backend.federated.strategies.fedavg_strategy import RoundResult
import logging

logger = logging.getLogger(__name__)

class QAPFLStrategy:
    def __init__(self):
        self.aggregator = QualityAwareAggregator()
        self.strategy_name = "QAPFL"
        self.last_audit: Optional[AggregationAudit] = None
    
    def compute_weights(self, clients: List[ClientMetadata]) -> Dict[str, float]:
        return self.aggregator.compute_weights(clients)
    
    def aggregate_weights(self, model_weights_list: List[Dict[str, np.ndarray]], client_weights: Dict[str, float]) -> Dict[str, np.ndarray]:
        return self.aggregator.aggregate_weights(model_weights_list, client_weights)
    
    def get_full_audit(self, clients: List[ClientMetadata]) -> AggregationAudit:
        self.last_audit = self.aggregator.full_audit(clients)
        return self.last_audit
