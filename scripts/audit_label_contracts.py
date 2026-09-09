"""Create an auditable summary of the frozen PTB-XL and MIT-BIH label rules."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datasets.mitbih import MITBIHDataset
from datasets.ptbxl import PTBXLDataset


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--ptbxl", default="data/raw/ptbxl")
	parser.add_argument("--mitbih", default="data/raw/mitbih")
	parser.add_argument("--output", default="experiments/label_audit_v1/label_contract_audit.json")
	args = parser.parse_args()
	ptbxl = PTBXLDataset(data_dir=args.ptbxl, target_lead="II", dataset_version="1.0.1")
	ptbxl_records = [record for record in ptbxl.load_all_records() if record.is_valid]
	mitbih = MITBIHDataset(data_dir=args.mitbih, target_lead="MLII")
	mitbih_windows = mitbih.build_windows(window_seconds=10, stride_seconds=5, target_fs=250)
	payload = {
		"audit_version": "1.0.0",
		"task": "NORMAL_MONITORED_PATTERN vs POTENTIALLY_ABNORMAL",
		"ptbxl": {
			"version": "1.0.1", "lead": "II", "records": len(ptbxl_records),
			"class_counts": dict(Counter(record.label_canonical for record in ptbxl_records)),
			"rule": "highest-confidence diagnostic superclass; NORM=normal and MI/STTC/CD/HYP=abnormal",
		},
		"mitbih": {
			"version": "1.0.0", "lead": "MLII", "windows": len(mitbih_windows),
			"class_counts": dict(Counter(mitbih_windows.label_canonical)),
			"rule": "10-second 250 Hz windows; majority valid beat label; ties and excluded-only windows dropped",
		},
		"comparability_limit": "PTB-XL diagnostic superclasses and MIT-BIH beat-rhythm annotations are different label sources; external evaluation is a generalization check, not a label-equivalence claim.",
	}
	output = Path(args.output)
	output.parent.mkdir(parents=True, exist_ok=True)
	output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
	main()
