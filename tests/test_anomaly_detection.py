from backend.ml.anomaly_detector import AnomalyDetector, AnomalyClassification
from backend.ml.models.isolation_forest import IFModel

def test_isolation_forest():
    model = IFModel()
    import numpy as np
    model.fit(np.random.randn(10, 3))
    preds = model.predict(np.random.randn(5, 3))
    assert len(preds) == 5

def test_anomaly_classification():
    det = AnomalyDetector(None)
    assert det.classify(0.9, 0.9, 90) == AnomalyClassification.HIGH_CONFIDENCE_ANOMALY
    assert det.classify(0.9, 0.9, 50) == AnomalyClassification.LOW_CONFIDENCE_EVENT