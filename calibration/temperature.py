"""Validation-only temperature scaling and threshold selection."""

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from sklearn.metrics import f1_score, recall_score


@dataclass
class TemperatureScaler:
    temperature: float = 1.0

    def fit(self, probabilities, labels) -> "TemperatureScaler":
        probabilities = np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1 - 1e-6)
        labels = np.asarray(labels, dtype=int)
        if len(probabilities) != len(labels) or len(np.unique(labels)) < 2:
            raise ValueError("Temperature scaling requires both classes and matching arrays")

        logits = logit(probabilities)

        def nll(log_temperature):
            scaled = logits / np.exp(log_temperature)
            return float(np.mean(np.maximum(scaled, 0) - scaled * labels + np.log1p(np.exp(-np.abs(scaled)))))

        result = minimize_scalar(nll, bounds=(-3.0, 3.0), method="bounded")
        if not result.success:
            raise RuntimeError(f"Temperature optimization failed: {result.message}")
        self.temperature = float(np.exp(result.x))
        return self

    def transform(self, probabilities):
        p = np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1 - 1e-6)
        return expit(logit(p) / self.temperature)

    def to_dict(self):
        return {"method": "temperature_scaling", "temperature": self.temperature}

    @classmethod
    def from_dict(cls, payload):
        return cls(temperature=float(payload["temperature"]))

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))


def select_f1_threshold(probabilities, labels):
    """Select validation threshold by F1, breaking ties toward sensitivity."""
    probabilities = np.asarray(probabilities, dtype=float)
    labels = np.asarray(labels, dtype=int)
    candidates = np.unique(np.concatenate(([0.5], probabilities)))
    scored = []
    for threshold in candidates:
        predictions = (probabilities >= threshold).astype(int)
        scored.append((
            float(f1_score(labels, predictions, zero_division=0)),
            float(recall_score(labels, predictions, zero_division=0)),
            float(threshold),
        ))
    # Max F1, then sensitivity, then higher threshold for deterministic output.
    return max(scored, key=lambda item: (item[0], item[1], item[2]))[2]
