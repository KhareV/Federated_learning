"""Validate the canonical NHM raw dataset layout.

Usage:
    python scripts/validate_datasets.py
    python scripts/validate_datasets.py --output data/manifests/dataset_inventory.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datasets.registry import inventory, load_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate NHM dataset roots")
    parser.add_argument("--output", default="data/manifests/dataset_inventory.json")
    args = parser.parse_args()

    report = inventory(load_registry(project_root=ROOT))
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for dataset in report["datasets"]:
        print(f"{dataset['name']}: {dataset['status']} ({dataset['root']})")
        for error in dataset["errors"]:
            print(f"  ERROR: {error}")
    print(f"Inventory written to {output}")
    return 0 if report["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())

