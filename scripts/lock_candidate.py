"""Create and verify an immutable evidence manifest for an ECG candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--preprocessing", required=True)
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--threshold", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--manifest", default="data/manifests/ptbxl_manifest.csv")
    parser.add_argument("--split", default="data/splits/ptbxl_splits.csv")
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    paths = {name: Path(value) for name, value in {
        "checkpoint": args.checkpoint, "preprocessing": args.preprocessing,
        "calibration": args.calibration, "threshold": args.threshold,
        "report": args.report, "dataset_manifest": args.manifest, "split_manifest": args.split,
    }.items()}
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing candidate artifacts: {', '.join(missing)}")
    output = Path(args.output)
    if args.verify:
        locked = json.loads(output.read_text())
        mismatches = [name for name, path in paths.items() if locked["artifacts"][name]["sha256"] != digest(path)]
        if mismatches:
            raise SystemExit(f"Candidate integrity mismatch: {', '.join(mismatches)}")
        print("candidate integrity verified")
        return
    report = json.loads(paths["report"].read_text())
    payload = {
        "model_version": args.model_version,
        "source_revision": revision(),
        "release_status": report.get("release_status", "UNKNOWN"),
        "external_release_gate": report.get("external_release_gate", {}),
        "artifacts": {name: {"path": str(path), "sha256": digest(path)} for name, path in paths.items()},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
