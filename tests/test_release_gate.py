from evaluation.release_gate import ExternalReleaseGate


def test_balanced_external_gate_requires_all_metrics():
	gate = ExternalReleaseGate()
	assert gate.evaluate({"auroc": 0.81, "recall": 0.70, "specificity": 0.70})["status"] == "PASS"
	result = gate.evaluate({"auroc": 0.81, "recall": 1.0, "specificity": 0.071})
	assert result["status"] == "FAIL"
	assert result["checks"]["specificity"] is False
