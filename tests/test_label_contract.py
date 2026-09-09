import numpy as np

from datasets.mitbih import majority_window_label


def test_mitbih_majority_vote_excludes_ties_and_artifact_only_windows():
	assert majority_window_label(np.array(["NORMAL", "ABNORMAL"])) is None
	assert majority_window_label(np.array(["EXCLUDE", "EXCLUDE"])) is None
	assert majority_window_label(np.array(["NORMAL", "NORMAL", "ABNORMAL"])) == "NORMAL"
	assert majority_window_label(np.array(["ABNORMAL", "ABNORMAL", "NORMAL"])) == "ABNORMAL"
