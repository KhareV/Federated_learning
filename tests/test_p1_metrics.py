"""
tests/test_p1_metrics.py — P1 Metrics Tests
=============================================
Tests compute_metrics to ensure correct calculation of:
  - Accuracy, Precision, Recall, F1, Specificity
  - Confusion matrix
  - AUROC, AUPRC (handling edge cases safely)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from evaluation.metrics import compute_metrics, ClassificationMetrics


class TestMetrics:

    def test_perfect_predictions(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        y_prob = np.array([0.1, 0.2, 0.8, 0.9])
        
        m = compute_metrics(y_true, y_pred, y_prob)
        assert m.accuracy == 1.0
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.f1 == 1.0
        assert m.specificity == 1.0
        assert m.auroc == 1.0
        assert m.auprc == 1.0
        assert m.tp == 2 and m.tn == 2 and m.fp == 0 and m.fn == 0

    def test_all_wrong_predictions(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 0, 0])
        y_prob = np.array([0.9, 0.8, 0.1, 0.2])
        
        m = compute_metrics(y_true, y_pred, y_prob)
        assert m.accuracy == 0.0
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1 == 0.0
        assert m.specificity == 0.0
        assert m.auroc == 0.0
        assert m.tp == 0 and m.tn == 0 and m.fp == 2 and m.fn == 2

    def test_no_probabilities_provided(self):
        y_true = np.array([0, 1])
        y_pred = np.array([0, 1])
        
        m = compute_metrics(y_true, y_pred)
        assert m.accuracy == 1.0
        assert m.auroc == -1.0
        assert m.auprc == -1.0

    def test_single_class_in_y_true(self):
        y_true = np.array([0, 0, 0])
        y_pred = np.array([0, 0, 1])
        y_prob = np.array([0.1, 0.2, 0.9])
        
        m = compute_metrics(y_true, y_pred, y_prob)
        assert pytest.approx(m.accuracy, abs=1e-3) == 2/3
        assert m.tp == 0
        assert m.fp == 1
        assert m.fn == 0
        assert m.tn == 2
        
        # AUROC/AUPRC should fail gracefully and return -1.0
        assert m.auroc == -1.0
        assert m.auprc == -1.0

    def test_to_dict(self):
        y_true = np.array([0, 1])
        y_pred = np.array([0, 1])
        m = compute_metrics(y_true, y_pred)
        d = m.to_dict()
        assert d["accuracy"] == 1.0
        assert d["split"] == "test"
