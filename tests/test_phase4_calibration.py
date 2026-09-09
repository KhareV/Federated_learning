import numpy as np

from calibration.temperature import TemperatureScaler, select_f1_threshold


def test_temperature_scaling_round_trip(tmp_path):
    probabilities = np.array([0.05, 0.2, 0.8, 0.95])
    labels = np.array([0, 0, 1, 1])
    scaler = TemperatureScaler().fit(probabilities, labels)
    assert scaler.temperature > 0
    path = tmp_path / "temperature.json"
    scaler.save(path)
    loaded = TemperatureScaler.load(path)
    np.testing.assert_allclose(scaler.transform(probabilities), loaded.transform(probabilities))


def test_threshold_maximizes_f1_then_sensitivity():
    probabilities = np.array([0.1, 0.2, 0.7, 0.8])
    labels = np.array([0, 0, 1, 1])
    assert select_f1_threshold(probabilities, labels) in {0.5, 0.7}


def test_threshold_is_deterministic_on_ties():
    probabilities = np.array([0.2, 0.4, 0.6, 0.8])
    labels = np.array([0, 1, 0, 1])
    assert select_f1_threshold(probabilities, labels) == select_f1_threshold(probabilities, labels)
