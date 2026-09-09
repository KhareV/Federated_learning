"""
training/train_ecg_cnn.py — 1D CNN Training (E04)
===================================================
Trains the ECGCNN1D model for binary ECG classification.

Usage:
  python training/train_ecg_cnn.py --synthetic
  python training/train_ecg_cnn.py --ptbxl data/raw/ptbxl

Output:
  experiments/E04_ecg_cnn/
    best_checkpoint.pt      — best validation checkpoint
    final_checkpoint.pt     — checkpoint at last epoch
    config.json             — full config for reproducibility
    training_log.json       — epoch-by-epoch metrics
    results.json            — final test metrics
"""

import sys
import json
import logging
import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from training.train_classical import (
    generate_synthetic_dataset,
    patient_level_split_synthetic,
    extract_features,
)
from preprocessing.ecg import ECGPreprocessor, NormalizationStats, synthesize_ecg_segment
from preprocessing.quality_ecg import ECGQualityAssessor
from models.ecg_cnn import ECGCNN1D, ECGCNNConfig, ECGWindowDataset
from evaluation.metrics import compute_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def prepare_windows(
    signals: np.ndarray,
    labels: np.ndarray,
    preprocessor: ECGPreprocessor,
    window_samples: int = 2500,
    source_fs: int = 250,
):
    """Preprocess raw signals → fixed-length windows for CNN."""
    X, y = [], []
    for sig, label in zip(signals, labels):
        prep = preprocessor.process(sig.astype(np.float32), source_fs)
        if not prep.is_valid:
            continue
        processed = prep.signal

        # Window: take first window_samples, pad if shorter
        if len(processed) >= window_samples:
            window = processed[:window_samples]
        else:
            window = np.pad(
                processed, (0, window_samples - len(processed)), mode="constant"
            )
        X.append(window.astype(np.float32))
        y.append(int(label))

    return np.array(X), np.array(y)


def train_epoch(
    model, loader, optimizer, criterion, device
) -> float:
    """Run one training epoch. Returns average loss."""
    model.train()
    total_loss = 0.0
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(y_batch)
    return total_loss / max(len(loader.dataset), 1)


@torch.no_grad()
def evaluate_epoch(
    model, loader, criterion, device
):
    """Evaluate on val/test. Returns (loss, y_true, y_pred, y_prob)."""
    model.eval()
    total_loss = 0.0
    all_true, all_pred, all_prob = [], [], []

    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        total_loss += loss.item() * len(y_batch)

        probs = torch.softmax(logits, dim=-1)
        preds = logits.argmax(dim=-1)

        all_true.extend(y_batch.cpu().numpy().tolist())
        all_pred.extend(preds.cpu().numpy().tolist())
        all_prob.extend(probs[:, 1].cpu().numpy().tolist())

    avg_loss = total_loss / max(len(loader.dataset), 1)
    return (
        avg_loss,
        np.array(all_true),
        np.array(all_pred),
        np.array(all_prob),
    )


def train_cnn(
    X_train, y_train,
    X_val, y_val,
    X_test, y_test,
    experiment_dir: str,
    dataset: str = "synthetic",
    seed: int = 42,
    batch_size: int = 32,
    max_epochs: int = 30,
    lr: float = 0.001,
    patience: int = 7,
    device: str = "auto",
    model_version: str = "MODEL_V1",
):
    """Full CNN training loop with early stopping and checkpointing."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    exp_dir = Path(experiment_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    # Class weights for imbalanced data
    n_total = len(y_train)
    n_normal = int(np.sum(y_train == 0))
    n_abnormal = int(np.sum(y_train == 1))
    class_weights = torch.tensor([
        n_total / (2 * n_normal + 1),
        n_total / (2 * n_abnormal + 1),
    ], dtype=torch.float32).to(device)

    # Config
    input_length = X_train.shape[1] if X_train.ndim > 1 else 2500
    config = ECGCNNConfig(
        input_length=input_length,
        model_version=model_version,
        preprocessing_version="1.0.0",
    )
    model = ECGCNN1D(config=config).to(device)
    logger.info(f"Model parameters: {model.count_parameters():,}")

    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max_epochs
    )
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # Datasets
    train_ds = ECGWindowDataset(X_train, y_train, augment=True)
    val_ds = ECGWindowDataset(X_val, y_val, augment=False)
    test_ds = ECGWindowDataset(X_test, y_test, augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=(device == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                             num_workers=0)

    # Training loop
    best_val_f1 = -1.0
    epochs_without_improvement = 0
    training_log = []
    t_start = time.time()

    for epoch in range(1, max_epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_true, val_pred, val_prob = evaluate_epoch(
            model, val_loader, criterion, device
        )
        val_metrics = compute_metrics(
            val_true, val_pred, val_prob, split="val",
            model_name="ecg_cnn", dataset=dataset
        )
        scheduler.step()

        logger.info(
            f"Epoch {epoch:3d}/{max_epochs} | "
            f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | "
            f"val_F1={val_metrics.f1:.4f} | val_AUROC={val_metrics.auroc:.4f}"
        )

        log_entry = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "val_loss": round(val_loss, 4),
            "val_accuracy": val_metrics.accuracy,
            "val_f1": val_metrics.f1,
            "val_recall": val_metrics.recall,
            "val_specificity": val_metrics.specificity,
            "val_auroc": val_metrics.auroc,
        }
        training_log.append(log_entry)

        # Checkpointing
        if val_metrics.f1 > best_val_f1:
            best_val_f1 = val_metrics.f1
            epochs_without_improvement = 0
            model.save_checkpoint(
                str(exp_dir / "best_checkpoint.pt"),
                epoch=epoch,
                metrics={"val_f1": val_metrics.f1, "val_auroc": val_metrics.auroc},
            )
            logger.info(f"  ★ New best val F1: {best_val_f1:.4f}")
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= patience:
            logger.info(f"Early stopping at epoch {epoch}")
            break

    # Save final checkpoint
    model.save_checkpoint(
        str(exp_dir / "final_checkpoint.pt"),
        epoch=epoch,
        metrics={"val_f1": best_val_f1},
    )

    total_time = time.time() - t_start
    logger.info(f"Training complete in {total_time:.1f}s")

    # ── Final Evaluation on test set ─────────────────────────────────────────
    # Load best model for test evaluation
    best_model, ckpt = ECGCNN1D.load_checkpoint(
        str(exp_dir / "best_checkpoint.pt"), device=device
    )
    test_loss, test_true, test_pred, test_prob = evaluate_epoch(
        best_model, test_loader, criterion, device
    )
    test_metrics = compute_metrics(
        test_true, test_pred, test_prob,
        split="test", model_name=f"ecg_cnn_{model_version}", dataset=dataset
    )
    test_metrics.print_report("E04 1D CNN — TEST SET")

    # Save config and results
    with open(exp_dir / "config.json", "w") as f:
        json.dump({
            "experiment": "E04_ecg_cnn",
            "model_version": model_version,
            "model_config": config.to_dict(),
            "training": {
                "seed": seed, "batch_size": batch_size,
                "max_epochs": max_epochs, "lr": lr,
                "patience": patience, "device": device,
                "training_time_s": round(total_time, 1),
                "epochs_run": epoch,
            },
            "dataset": dataset,
            "n_train": len(y_train),
            "n_val": len(y_val),
            "n_test": len(y_test),
        }, f, indent=2)

    with open(exp_dir / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)

    with open(exp_dir / "results.json", "w") as f:
        json.dump({
            "experiment": "E04_ecg_cnn", "model_version": model_version,
            "best_val_f1": round(best_val_f1, 4),
            "test": test_metrics.to_dict(),
        }, f, indent=2)

    logger.info(f"E04 results saved to {exp_dir}")
    return test_metrics, best_model


def main():
    parser = argparse.ArgumentParser(description="P1 CNN Training (E04)")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--ptbxl", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--patience", type=int, default=7)
    parser.add_argument("--output-dir", type=str, default="experiments")
    args = parser.parse_args()

    preprocessor = ECGPreprocessor()

    if args.ptbxl:
        logger.info(f"Loading PTB-XL from {args.ptbxl}...")
        from datasets.ptbxl import PTBXLDataset
        ds = PTBXLDataset(data_dir=args.ptbxl)
        if not ds.is_available():
            logger.error("PTB-XL not found. Use --synthetic.")
            sys.exit(1)
        manifest = ds.build_manifest()
        manifest = ds.generate_splits(manifest, seed=args.seed)
        # Load signals per split
        all_sigs, all_labels, all_pids = [], [], []
        for _, row in manifest.iterrows():
            try:
                recs = [r for r in ds.load_all_records()
                        if r.record_id == row["record_id"]]
                if not recs:
                    continue
                sig, fs = ds.load_signal(recs[0])
                all_sigs.append(sig)
                all_labels.append(int(row["label_int"]))
                all_pids.append(row["participant_id"])
            except Exception as exc:
                logger.warning(f"Skip: {exc}")
        signals = np.array(all_sigs)
        labels = np.array(all_labels)
        pids = all_pids
        source_fs = 500
        dataset_name = "ptbxl"
    else:
        logger.info("Using SYNTHETIC data (not for reporting results).")
        signals, labels, pids = generate_synthetic_dataset(seed=args.seed)
        source_fs = 250
        dataset_name = "SYNTHETIC"

    splits = patient_level_split_synthetic(pids, labels, seed=args.seed)
    train_idx = splits["train"]
    val_idx = splits["val"]
    test_idx = splits["test"]

    logger.info("Preparing CNN windows (preprocessing + windowing)...")
    X_train, y_train = prepare_windows(signals[train_idx], labels[train_idx],
                                        preprocessor, source_fs=source_fs)
    X_val, y_val = prepare_windows(signals[val_idx], labels[val_idx],
                                    preprocessor, source_fs=source_fs)
    X_test, y_test = prepare_windows(signals[test_idx], labels[test_idx],
                                      preprocessor, source_fs=source_fs)

    logger.info(f"CNN windows: train={X_train.shape}, val={X_val.shape}, "
                f"test={X_test.shape}")

    train_cnn(
        X_train, y_train, X_val, y_val, X_test, y_test,
        experiment_dir=f"{args.output_dir}/E04_ecg_cnn",
        dataset=dataset_name,
        seed=args.seed,
        batch_size=args.batch_size,
        max_epochs=args.epochs,
        lr=args.lr,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
