"""
tests/test_p1_inference.py — P1 Inference Interface Tests
===========================================================
Tests the ECGInferenceEngine:
  - Integration of preprocessor, SQI, and dummy model
  - Output format matches ECGInferenceResult
  - Batch prediction
  - FL reliability metadata format (NO raw signals)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from inference.ecg_inference import ECGInferenceEngine, ECGInferenceResult
from preprocessing.ecg import synthesize_ecg_segment


@pytest.fixture
def engine():
    # Uses dummy predictor since no model_path is provided
    return ECGInferenceEngine()


@pytest.fixture
def raw_signal():
    return synthesize_ecg_segment(3000, 250, seed=1)


class TestECGInferenceEngine:

    def test_predict_returns_result_object(self, engine, raw_signal):
        result = engine.predict(raw_signal, 250)
        assert isinstance(result, ECGInferenceResult)

    def test_predict_formats_correctly(self, engine, raw_signal):
        result = engine.predict(
            raw_signal, 250, record_id="test1", source_dataset="ptbxl"
        )
        assert result.record_id == "test1"
        assert result.source_dataset == "ptbxl"
        assert result.prediction in ("NORMAL", "ABNORMAL")
        assert result.prediction_int in (0, 1)
        assert 0.0 <= result.probability_normal <= 1.0
        assert 0.0 <= result.probability_abnormal <= 1.0
        assert 0.0 <= result.signal_quality_score <= 100.0
        assert result.signal_quality_state in ("EXCELLENT", "GOOD", "FAIR", "POOR")
        assert result.sampling_rate == 250
        assert result.window_samples == 2500

    def test_to_dict_includes_disclaimer(self, engine, raw_signal):
        result = engine.predict(raw_signal, 250)
        d = result.to_dict()
        assert "disclaimer" in d
        assert "NOT a medical diagnosis" in d["disclaimer"]

    def test_to_api_response_compact(self, engine, raw_signal):
        result = engine.predict(raw_signal, 250)
        d = result.to_api_response()
        assert d["disclaimer"] == "See full disclaimer in API docs"

    def test_predict_batch(self, engine):
        signals = [synthesize_ecg_segment(2500, 250, seed=i) for i in range(3)]
        results = engine.predict_batch(signals, 250)
        assert len(results) == 3
        assert all(isinstance(r, ECGInferenceResult) for r in results)

    def test_fl_reliability_metadata(self, engine):
        signals = [synthesize_ecg_segment(2500, 250, seed=i) for i in range(5)]
        meta = engine.get_fl_reliability_metadata(
            signals, 250, client_id="client_42", local_f1=0.85
        )
        # Check critical privacy boundary: no signals allowed
        assert "signals" not in meta
        assert "raw_signals" not in meta

        # Check required QAPFL fields
        assert meta["client_id"] == "client_42"
        assert meta["num_samples"] == 5
        assert 0.0 <= meta["mean_sqi"] <= 100.0
        assert "quality_distribution" in meta
        assert meta["local_f1"] == 0.85
        assert "mean_confidence" in meta
        assert "uncertainty_proxy" in meta
