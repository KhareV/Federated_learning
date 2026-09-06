from typing import List
from backend.federated.aggregation.quality_aggregator import ClientMetadata

class FLClientManager:
    def register_client(self, client_id, meta): pass
    def update_client_metrics(self, client_id, metrics): pass
    def get_client(self, client_id) -> ClientMetadata:
        return ClientMetadata(client_id, {}, 100, 100, 80, 80, 0.9, 0.9, 0.1, 0.1, 1.0, 0.0)
    def get_all_clients(self) -> List[ClientMetadata]: return []
    def select_clients_for_round(self, min_sqi=None) -> List[str]: return []