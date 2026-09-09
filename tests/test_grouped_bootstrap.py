import numpy as np

from evaluation.metrics import grouped_bootstrap_confidence_intervals


def test_grouped_bootstrap_reports_intervals_from_whole_groups():
    result = grouped_bootstrap_confidence_intervals(
        np.array([0, 0, 1, 1, 0, 1]), np.array([0, 0, 1, 1, 1, 1]),
        np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.8]), np.array(["a", "a", "b", "b", "c", "c"]), n_resamples=20,
    )
    assert set(result) == {"auroc", "recall", "specificity", "f1"}
    assert result["auroc"]["n_resamples"] > 0
