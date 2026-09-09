import numpy as np

from datasets.mitbih import majority_window_label
from datasets.ptbxl import PTBXLDataset


def test_mitbih_majority_vote_excludes_ties_and_artifact_only_windows():
	assert majority_window_label(np.array(["NORMAL", "ABNORMAL"])) is None
	assert majority_window_label(np.array(["EXCLUDE", "EXCLUDE"])) is None
	assert majority_window_label(np.array(["NORMAL", "NORMAL", "ABNORMAL"])) == "NORMAL"
	assert majority_window_label(np.array(["ABNORMAL", "ABNORMAL", "NORMAL"])) == "ABNORMAL"


def test_rhythm_conduction_task_uses_positive_scp_statements_only():
	dataset = PTBXLDataset(label_mode="rhythm_conduction")
	raw, label = dataset.resolve_label({"NORM": 100.0, "SBRAD": 0.0}, None)
	assert (raw, label) == ("NORM", "NORMAL")
	raw, label = dataset.resolve_label({"NORM": 80.0, "PVC": 100.0}, None)
	assert raw == "RHYTHM_CONDUCTION:PVC"
	assert label == "ABNORMAL"
	assert dataset.resolve_label({"MI": 100.0}, None) == (None, None)
