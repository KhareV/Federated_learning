"""
scripts/run_p1_pipeline.py — Master script to run all P1 training.
====================================================================
Runs the full P1 evaluation pipeline:
  1. Train Classical Baselines (Majority, LR, RF)
  2. Train 1D CNN

Usage:
  python scripts/run_p1_pipeline.py --synthetic
  python scripts/run_p1_pipeline.py --ptbxl data/raw/ptbxl
"""

import sys
import subprocess
from pathlib import Path
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def run_command(cmd_args):
    logging.info(f"Running: {' '.join(cmd_args)}")
    result = subprocess.run(cmd_args, text=True)
    if result.returncode != 0:
        logging.error(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="Run with synthetic data")
    parser.add_argument("--ptbxl", type=str, help="Path to PTB-XL")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    cmd_base = [sys.executable]
    
    data_args = ["--synthetic"] if args.synthetic else ["--ptbxl", args.ptbxl] if args.ptbxl else ["--synthetic"]

    logging.info("=== 1. Training Classical Models ===")
    run_command(cmd_base + [str(project_root / "training" / "train_classical.py")] + data_args)

    logging.info("=== 2. Training 1D CNN ===")
    run_command(cmd_base + [str(project_root / "training" / "train_ecg_cnn.py"), "--epochs", "5"] + data_args)

    logging.info("=== P1 Pipeline Complete ===")
    logging.info("Results saved to experiments/ directory.")

if __name__ == "__main__":
    main()
