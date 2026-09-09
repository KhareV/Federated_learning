"""
evaluation/metrics.py — P1 Classification Metrics
===================================================
Canonical metrics computation for all P1 experiments.

Includes:
  - Accuracy, Precision, Recall (Sensitivity), F1
  - Specificity, False Positive Rate
  - AUROC, AUPRC
  - Confusion matrix
  - Class-wise metrics
  - Formatted report

Design principles:
  - All metrics computed on the SAME held-out set
  - No test-set tuning
  - Imbalanced dataset aware (F1, AUROC, AUPRC)
  - Machine-readable dict output
  - Human-readable formatted report
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClassificationMetrics:
    """
    Complete binary classification metrics.
    All values are floats in [0, 1] unless noted.
    """
    # Core
    accuracy: float
    precision: float          # PPV (for ABNORMAL class)
    recall: float             # Sensitivity / TPR
    f1: float
    specificity: float        # TNR (NORMAL correctly classified)
    false_positive_rate: float  # FPR = 1 - specificity

    # Threshold-independent
    auroc: float              # Area Under ROC Curve
    auprc: float              # Area Under Precision-Recall Curve

    # Confusion matrix components
    tp: int
    tn: int
    fp: int
    fn: int
    n_total: int
    n_normal: int
    n_abnormal: int

    # Meta
    split: str = "test"
    model_name: str = "unknown"
    dataset: str = "unknown"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def print_report(self, title: str = "Classification Metrics"):
        """Pretty-print a human-readable report."""
        print("=" * 60)
        print(f" {title}")
        print("=" * 60)
        print(f"  Split:        {self.split}")
        print(f"  Model:        {self.model_name}")
        print(f"  Dataset:      {self.dataset}")
        print(f"  N Total:      {self.n_total} "
              f"(NORMAL={self.n_normal}, ABNORMAL={self.n_abnormal})")
        print()
        print(f"  Accuracy:     {self.accuracy:.4f}")
        print(f"  Precision:    {self.precision:.4f}")
        print(f"  Recall:       {self.recall:.4f}  ← Sensitivity")
        print(f"  F1:           {self.f1:.4f}")
        print(f"  Specificity:  {self.specificity:.4f}")
        print(f"  FPR:          {self.false_positive_rate:.4f}")
        print(f"  AUROC:        {self.auroc:.4f}")
        print(f"  AUPRC:        {self.auprc:.4f}")
        print()
        print("  Confusion Matrix:")
        print(f"              Pred NORMAL  Pred ABNORMAL")
        print(f"  True NORMAL     {self.tn:5d}         {self.fp:5d}")
        print(f"  True ABNORMAL   {self.fn:5d}         {self.tp:5d}")
        if self.notes:
            print(f"\n  Notes: {self.notes}")
        print("=" * 60)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    split: str = "test",
    model_name: str = "unknown",
    dataset: str = "unknown",
    notes: str = "",
    positive_class: int = 1,  # ABNORMAL = 1
) -> ClassificationMetrics:
    """
    Compute all binary classification metrics.

    Parameters
    ----------
    y_true : np.ndarray (n_samples,) — integer labels (0=NORMAL, 1=ABNORMAL)
    y_pred : np.ndarray (n_samples,) — predicted integer labels
    y_prob : np.ndarray (n_samples,) — predicted probability for positive class
             Required for AUROC/AUPRC. If None, these are set to -1.
    split : str — "train" | "val" | "test"
    model_name : str
    dataset : str
    notes : str

    Returns
    -------
    ClassificationMetrics
    """
    from sklearn.metrics import (
        confusion_matrix, precision_score, recall_score,
        f1_score, roc_auc_score, average_precision_score,
    )

    y_true = np.array(y_true).flatten().astype(int)
    y_pred = np.array(y_pred).flatten().astype(int)

    n_total = len(y_true)
    n_normal = int(np.sum(y_true == 0))
    n_abnormal = int(np.sum(y_true == 1))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    tn, fp, fn, tp = int(tn), int(fp), int(fn), int(tp)

    accuracy = (tp + tn) / (n_total + 1e-9)
    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)       # Sensitivity
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    specificity = tn / (tn + fp + 1e-9)  # TNR
    fpr = fp / (fp + tn + 1e-9)

    # Threshold-independent metrics
    if y_prob is not None and len(np.unique(y_true)) == 2:
        try:
            auroc = float(roc_auc_score(y_true, y_prob))
        except Exception as exc:
            logger.warning(f"AUROC failed: {exc}")
            auroc = -1.0
        try:
            auprc = float(average_precision_score(y_true, y_prob))
        except Exception as exc:
            logger.warning(f"AUPRC failed: {exc}")
            auprc = -1.0
    else:
        auroc = -1.0
        auprc = -1.0

    return ClassificationMetrics(
        accuracy=round(float(accuracy), 4),
        precision=round(float(precision), 4),
        recall=round(float(recall), 4),
        f1=round(float(f1), 4),
        specificity=round(float(specificity), 4),
        false_positive_rate=round(float(fpr), 4),
        auroc=round(float(auroc), 4),
        auprc=round(float(auprc), 4),
        tp=tp, tn=tn, fp=fp, fn=fn,
        n_total=n_total, n_normal=n_normal, n_abnormal=n_abnormal,
        split=split, model_name=model_name, dataset=dataset, notes=notes,
    )


def compute_per_class_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: List[str] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Per-class precision, recall, F1.

    Returns
    -------
    {class_name: {"precision": ..., "recall": ..., "f1": ..., "support": ...}}
    """
    from sklearn.metrics import classification_report
    if class_names is None:
        class_names = ["NORMAL", "ABNORMAL"]

    report = classification_report(
        y_true, y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    result = {}
    for cls in class_names:
        if cls in report:
            result[cls] = {
                "precision": round(report[cls]["precision"], 4),
                "recall": round(report[cls]["recall"], 4),
                "f1": round(report[cls]["f1-score"], 4),
                "support": int(report[cls]["support"]),
            }
    return result


def grouped_bootstrap_confidence_intervals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    groups: np.ndarray,
    n_resamples: int = 500,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """95% percentile intervals resampling whole participants/records.

    Windows within a recording are correlated. Resampling rows would produce
    misleadingly narrow intervals, so one bootstrap draw samples groups and
    retains all of their windows.
    """
    y_true, y_pred, y_prob, groups = map(np.asarray, (y_true, y_pred, y_prob, groups))
    unique = np.unique(groups)
    if len(unique) < 2:
        return {}
    rng = np.random.default_rng(seed)
    values: Dict[str, list[float]] = {name: [] for name in ("auroc", "recall", "specificity", "f1")}
    for _ in range(n_resamples):
        chosen = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == group) for group in chosen])
        sample = compute_metrics(y_true[indices], y_pred[indices], y_prob[indices])
        for name in values:
            if getattr(sample, name) >= 0:
                values[name].append(float(getattr(sample, name)))
    return {
        name: {"lower_95": round(float(np.quantile(samples, 0.025)), 4), "upper_95": round(float(np.quantile(samples, 0.975)), 4), "n_resamples": len(samples)}
        for name, samples in values.items() if samples
    }
