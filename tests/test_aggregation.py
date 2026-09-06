from backend.federated.aggregation.quality_aggregator import QualityAwareAggregator, ClientMetadata
import numpy as np

def test_qapfl_weights_reflect_quality():
    agg = QualityAwareAggregator()
    c1 = ClientMetadata("c1", {}, 100, 100, 90, 90, 0.9, 0.9, 0.1, 0.1, 1.0, 0.0)
    c2 = ClientMetadata("c2", {}, 100, 100, 30, 30, 0.5, 0.5, 0.5, 0.5, 1.0, 0.0)
    weights = agg.compute_weights([c1, c2])
    assert weights["c1"] > weights["c2"]

def test_weights_sum_to_one():
    agg = QualityAwareAggregator()
    c1 = ClientMetadata("c1", {}, 100, 100, 90, 90, 0.9, 0.9, 0.1, 0.1, 1.0, 0.0)
    c2 = ClientMetadata("c2", {}, 100, 100, 30, 30, 0.5, 0.5, 0.5, 0.5, 1.0, 0.0)
    weights = agg.compute_weights([c1, c2])
    assert np.isclose(sum(weights.values()), 1.0)