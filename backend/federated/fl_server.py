import numpy as np
import time
import uuid
import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from backend.federated.aggregation.quality_aggregator import ClientMetadata
from backend.federated.strategies.fedavg_strategy import FedAvgStrategy, RoundResult
from backend.federated.strategies.personalized_strategy import PersonalizedFLStrategy
from backend.federated.strategies.qapfl_strategy import QAPFLStrategy

logger = logging.getLogger(__name__)

class FLServer:
    def __init__(self):
        self.strategies = {
            "fedavg": FedAvgStrategy(),
            "personalized": PersonalizedFLStrategy(),
            "qapfl": QAPFLStrategy(),
        }
        self.current_round = 0
        self.round_history: List[RoundResult] = []
        self.is_training = False
        self._global_model_weights = self._init_model_weights()
        self._progress_callback = None
    
    def _init_model_weights(self) -> Dict[str, np.ndarray]:
        rng = np.random.RandomState(42)
        return {
            "lstm_encoder.weight_ih": rng.randn(128, 32).astype(np.float32) * 0.1,
            "lstm_encoder.weight_hh": rng.randn(128, 32).astype(np.float32) * 0.1,
            "lstm_encoder.bias": rng.randn(128).astype(np.float32) * 0.01,
            "lstm_decoder.weight_ih": rng.randn(128, 32).astype(np.float32) * 0.1,
            "lstm_decoder.weight_hh": rng.randn(128, 32).astype(np.float32) * 0.1,
            "lstm_decoder.bias": rng.randn(128).astype(np.float32) * 0.01,
            "output_layer.weight": rng.randn(32, 128).astype(np.float32) * 0.1,
            "output_layer.bias": rng.randn(32).astype(np.float32) * 0.01,
        }
    
    def _simulate_local_training(self, client: ClientMetadata, global_weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        rng = np.random.RandomState(hash(client.client_id) % (2**31))
        avg_sqi = (client.ecg_sqi + client.ppg_sqi) / 2
        noise_scale = 0.05 * (1.0 - avg_sqi / 100.0) + 0.001
        
        local_weights = {}
        for name, weights in global_weights.items():
            update = rng.normal(0, noise_scale, weights.shape).astype(np.float32)
            local_weights[name] = weights + update
        return local_weights
    
    def _simulate_client_metrics(self, client: ClientMetadata, round_number: int) -> Dict[str, float]:
        rng = np.random.RandomState(hash(f"{client.client_id}_{round_number}") % (2**31))
        avg_sqi = (client.ecg_sqi + client.ppg_sqi) / 2
        base_accuracy = 0.70 + (avg_sqi / 100) * 0.20
        base_f1 = 0.68 + (avg_sqi / 100) * 0.22
        round_bonus = min(round_number * 0.008, 0.06)
        
        accuracy = np.clip(base_accuracy + round_bonus + rng.normal(0, 0.02), 0.4, 0.98)
        f1 = np.clip(base_f1 + round_bonus + rng.normal(0, 0.025), 0.4, 0.98)
        loss = max(0.05, (1.0 - accuracy) * 0.8 + rng.uniform(0, 0.05))
        uncertainty = np.clip(rng.normal(client.uncertainty, 0.05), 0.0, 1.0)
        
        return {
            "local_accuracy": float(accuracy),
            "local_f1": float(f1),
            "local_loss": float(loss),
            "uncertainty": float(uncertainty),
        }
    
    def run_round(self, strategy_name: str, clients: List[ClientMetadata], round_number: Optional[int] = None) -> RoundResult:
        if round_number is None:
            self.current_round += 1
            round_number = self.current_round
        
        strategy = self.strategies.get(strategy_name, self.strategies["fedavg"])
        start_time = time.time()
        
        logger.info(f"FL Round {round_number} starting | Strategy: {strategy_name} | Clients: {len(clients)}")
        
        local_metrics_list = []
        local_weights_list = []
        updated_clients = []
        
        for client in clients:
            metrics = self._simulate_client_metrics(client, round_number)
            local_metrics_list.append(metrics)
            
            updated_client = ClientMetadata(
                client_id=client.client_id,
                profile=client.profile,
                dataset_size=client.dataset_size,
                usable_samples=client.usable_samples,
                ecg_sqi=client.ecg_sqi,
                ppg_sqi=client.ppg_sqi,
                local_accuracy=metrics["local_accuracy"],
                local_f1=metrics["local_f1"],
                local_loss=metrics["local_loss"],
                uncertainty=metrics["uncertainty"],
                battery_level=client.battery_level,
                last_participation=time.time(),
                aggregation_weight=0.0
            )
            updated_clients.append(updated_client)
            local_weights_list.append(self._simulate_local_training(updated_client, self._global_model_weights))
        
        weights = strategy.compute_weights(updated_clients)
        
        if local_weights_list:
            self._global_model_weights = strategy.aggregate_weights(local_weights_list, weights)
        
        rng = np.random.RandomState(round_number * 7)
        avg_local_accuracy = np.mean([m["local_accuracy"] for m in local_metrics_list])
        avg_local_f1 = np.mean([m["local_f1"] for m in local_metrics_list])
        avg_local_loss = np.mean([m["local_loss"] for m in local_metrics_list])
        
        global_accuracy = min(0.98, avg_local_accuracy + 0.02 + rng.uniform(0, 0.01))
        global_f1 = min(0.98, avg_local_f1 + 0.02 + rng.uniform(0, 0.01))
        global_loss = max(0.02, avg_local_loss - 0.05)
        
        avg_sqi = np.mean([(c.ecg_sqi + c.ppg_sqi) / 2 for c in updated_clients])
        
        total_params = sum(w.size for w in self._global_model_weights.values())
        comm_cost = total_params * 4 * len(clients)
        
        training_time = time.time() - start_time
        
        reasoning = None
        if strategy_name == "qapfl" and hasattr(strategy, 'get_full_audit'):
            audit = strategy.get_full_audit(updated_clients)
            reasoning = audit.client_reasoning
        
        result = RoundResult(
            round_number=round_number,
            strategy=strategy_name,
            participating_client_ids=[c.client_id for c in updated_clients],
            avg_local_loss=float(avg_local_loss),
            avg_local_accuracy=float(avg_local_accuracy),
            avg_local_f1=float(avg_local_f1),
            global_accuracy=float(global_accuracy),
            global_f1=float(global_f1),
            global_loss=float(global_loss),
            avg_sqi=float(avg_sqi),
            communication_cost_bytes=int(comm_cost),
            training_time_seconds=float(training_time),
            aggregation_weights=weights,
            aggregation_reasoning=reasoning
        )
        
        self.round_history.append(result)
        logger.info(f"FL Round {round_number} complete | Global accuracy: {global_accuracy:.4f} | F1: {global_f1:.4f}")
        return result
    
    async def run_experiment(self, strategy_name: str, n_rounds: int, clients: List[ClientMetadata], progress_callback=None) -> List[RoundResult]:
        self.is_training = True
        self.current_round = 0
        self._global_model_weights = self._init_model_weights()
        results = []
        
        for i in range(n_rounds):
            result = self.run_round(strategy_name, clients, round_number=i+1)
            results.append(result)
            
            if progress_callback:
                await progress_callback({"round": i+1, "total": n_rounds, "result": result})
            
            await asyncio.sleep(0)
        
        self.is_training = False
        return results
