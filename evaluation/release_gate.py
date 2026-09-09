"""Pre-registered release gates for a frozen centralized ECG candidate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ExternalReleaseGate:
	"""Balanced MIT-BIH gate; the dataset remains evaluation-only."""
	auroc_min: float = 0.80
	sensitivity_min: float = 0.70
	specificity_min: float = 0.70

	def evaluate(self, metrics: Mapping[str, float]) -> dict:
		required = {"auroc": self.auroc_min, "recall": self.sensitivity_min, "specificity": self.specificity_min}
		missing = sorted(set(required) - set(metrics))
		checks = {name: float(metrics[name]) >= threshold for name, threshold in required.items() if name in metrics}
		return {
			"status": "PASS" if not missing and all(checks.values()) else "FAIL",
			"thresholds": {"auroc": self.auroc_min, "sensitivity": self.sensitivity_min, "specificity": self.specificity_min},
			"observed": {"auroc": metrics.get("auroc"), "sensitivity": metrics.get("recall"), "specificity": metrics.get("specificity")},
			"checks": checks,
			"missing_metrics": missing,
		}
