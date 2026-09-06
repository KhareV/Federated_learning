"""
datasets/ptbxl.py — PTB-XL Dataset Loader
==========================================
Loads the PTB-XL ECG dataset (PhysioNet, v1.0.2) using WFDB.

Official source:
  https://physionet.org/content/ptb-xl/1.0.2/

Expected local path (configurable):
  data/raw/ptbxl/

Download instructions:
  pip install wfdb
  python -c "import wfdb; wfdb.dl_database('ptb-xl', dl_dir='data/raw/ptbxl')"
  -- OR --
  wget -r -N -c -np https://physionet.org/files/ptb-xl/1.0.2/ -P data/raw/ptbxl

Canonical label mapping:
  NORM  → NORMAL  (0)
  MI    → ABNORMAL (1)
  STTC  → ABNORMAL (1)
  CD    → ABNORMAL (1)
  HYP   → ABNORMAL (1)

Preprocessing version: read from configs/ecg_preprocessing.yaml
"""

import os
import logging
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── Canonical Label Mapping ──────────────────────────────────────────────────

PTBXL_SUPERCLASS_TO_CANONICAL = {
    "NORM": "NORMAL",
    "MI":   "ABNORMAL",
    "STTC": "ABNORMAL",
    "CD":   "ABNORMAL",
    "HYP":  "ABNORMAL",
}

CANONICAL_TO_INT = {"NORMAL": 0, "ABNORMAL": 1}

# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class PTBXLRecord:
    """Canonical representation of a single PTB-XL ECG record."""
    record_id: str                     # e.g. "records500/00000/00001_hr"
    participant_id: str                # patient_id from metadata
    ecg_id: int                        # ecg_id from ptbxl_database.csv
    sampling_rate: int                 # Hz (100 or 500)
    n_samples: int                     # number of samples in record
    n_leads: int                       # 12
    lead_names: List[str]              # ['I', 'II', ...]
    label_raw: str                     # original superclass e.g. "NORM"
    label_canonical: str               # "NORMAL" or "ABNORMAL"
    label_int: int                     # 0 or 1
    age: Optional[float] = None
    sex: Optional[str] = None
    source_dataset: str = "ptbxl"
    dataset_version: str = "1.0.2"
    file_path: str = ""
    is_valid: bool = True
    validation_notes: List[str] = field(default_factory=list)


@dataclass
class PTBXLValidationReport:
    """Summary of dataset validation."""
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    n_patients: int = 0
    n_normal: int = 0
    n_abnormal: int = 0
    n_excluded: int = 0
    sampling_rate_distribution: Dict[int, int] = field(default_factory=dict)
    invalid_reasons: Dict[str, int] = field(default_factory=dict)
    patient_record_counts: Dict[str, int] = field(default_factory=dict)


# ─── PTB-XL Dataset Class ────────────────────────────────────────────────────

class PTBXLDataset:
    """
    PTB-XL Dataset loader with validation, manifest generation,
    and patient-level splitting support.

    Parameters
    ----------
    data_dir : str
        Path to the root of the PTB-XL dataset
        (should contain ptbxl_database.csv and records500/ or records100/).
    sampling_rate : int
        Which PTB-XL sampling rate to use: 100 or 500.
    target_lead : str
        Which lead to use as the primary single-channel signal (e.g. 'II').
    preprocessing_version : str
        Version string injected into manifest rows for traceability.
    """

    LEAD_NAMES = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF',
                  'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

    def __init__(
        self,
        data_dir: str = "data/raw/ptbxl",
        sampling_rate: int = 500,
        target_lead: str = "II",
        preprocessing_version: str = "1.0.0",
    ):
        self.data_dir = Path(data_dir)
        self.sampling_rate = sampling_rate
        self.target_lead = target_lead
        self.preprocessing_version = preprocessing_version
        self._records: Optional[List[PTBXLRecord]] = None
        self._metadata_df: Optional[pd.DataFrame] = None
        self._scp_statements: Optional[pd.DataFrame] = None

        # Validate lead
        if target_lead not in self.LEAD_NAMES:
            raise ValueError(f"Unknown lead '{target_lead}'. "
                             f"Valid: {self.LEAD_NAMES}")
        self._lead_idx = self.LEAD_NAMES.index(target_lead)

    # ── Path helpers ─────────────────────────────────────────────────────────

    @property
    def metadata_path(self) -> Path:
        return self.data_dir / "ptbxl_database.csv"

    @property
    def scp_statements_path(self) -> Path:
        return self.data_dir / "scp_statements.csv"

    @property
    def records_subdir(self) -> str:
        return f"records{self.sampling_rate}"

    def is_available(self) -> bool:
        """Return True if the dataset appears to be downloaded."""
        return (self.metadata_path.exists() and
                (self.data_dir / self.records_subdir).exists())

    # ── Metadata Loading ─────────────────────────────────────────────────────

    def load_metadata(self) -> pd.DataFrame:
        """Load ptbxl_database.csv and parse SCP label columns."""
        if self._metadata_df is not None:
            return self._metadata_df

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"PTB-XL metadata not found at {self.metadata_path}. "
                f"Please download the dataset:\n"
                f"  python -c \"import wfdb; wfdb.dl_database('ptb-xl', "
                f"dl_dir='{self.data_dir}')\""
            )

        df = pd.read_csv(self.metadata_path, index_col="ecg_id")
        # Parse the scp_codes JSON column
        df["scp_codes"] = df["scp_codes"].apply(
            lambda x: json.loads(x.replace("'", '"')) if isinstance(x, str) else {}
        )
        self._metadata_df = df
        logger.info(f"Loaded PTB-XL metadata: {len(df)} records")
        return df

    def load_scp_statements(self) -> pd.DataFrame:
        """Load scp_statements.csv which maps SCP codes to diagnostic classes."""
        if self._scp_statements is not None:
            return self._scp_statements
        if not self.scp_statements_path.exists():
            raise FileNotFoundError(
                f"SCP statements file not found at {self.scp_statements_path}"
            )
        df = pd.read_csv(self.scp_statements_path, index_col=0)
        self._scp_statements = df
        return df

    # ── Label Resolution ─────────────────────────────────────────────────────

    def resolve_superclass(self, scp_codes: dict, scp_df: pd.DataFrame) -> Optional[str]:
        """
        Determine the dominant superclass for a record from its SCP codes.
        Returns the superclass string (e.g. 'NORM', 'MI') or None if ambiguous/unknown.
        """
        if not scp_codes:
            return None

        # Collect superclasses with their confidence scores
        superclass_scores: Dict[str, float] = {}
        for code, confidence in scp_codes.items():
            if code in scp_df.index:
                sc = scp_df.loc[code, "diagnostic_class"]
                if isinstance(sc, str) and sc.strip():
                    superclass_scores[sc.strip()] = max(
                        superclass_scores.get(sc.strip(), 0), confidence
                    )

        if not superclass_scores:
            return None

        # Pick the highest-confidence superclass
        return max(superclass_scores, key=superclass_scores.get)

    # ── Record Loading ────────────────────────────────────────────────────────

    def load_all_records(self, max_records: Optional[int] = None) -> List[PTBXLRecord]:
        """
        Discover and parse all valid PTB-XL records.
        Results are cached after first call.

        Parameters
        ----------
        max_records : int, optional
            Limit for development/testing. None = load all.
        """
        if self._records is not None:
            return self._records

        meta_df = self.load_metadata()
        scp_df = self.load_scp_statements()

        records = []
        rows = list(meta_df.iterrows())
        if max_records:
            rows = rows[:max_records]

        for ecg_id, row in rows:
            try:
                record = self._parse_record(ecg_id, row, scp_df)
                records.append(record)
            except Exception as exc:
                logger.warning(f"Skipped ecg_id={ecg_id}: {exc}")
                records.append(PTBXLRecord(
                    record_id=str(ecg_id),
                    participant_id=str(row.get("patient_id", "unknown")),
                    ecg_id=int(ecg_id),
                    sampling_rate=self.sampling_rate,
                    n_samples=0,
                    n_leads=12,
                    lead_names=self.LEAD_NAMES,
                    label_raw="UNKNOWN",
                    label_canonical="UNKNOWN",
                    label_int=-1,
                    is_valid=False,
                    validation_notes=[str(exc)],
                ))

        self._records = records
        logger.info(
            f"Loaded {len(records)} records "
            f"({sum(r.is_valid for r in records)} valid)"
        )
        return records

    def _parse_record(self, ecg_id: int, row: pd.Series,
                      scp_df: pd.DataFrame) -> PTBXLRecord:
        """Parse a single record row into a PTBXLRecord."""
        # Resolve label
        scp_codes = row.get("scp_codes", {})
        if not isinstance(scp_codes, dict):
            scp_codes = {}

        superclass = self.resolve_superclass(scp_codes, scp_df)
        if superclass is None:
            raise ValueError(f"Could not resolve superclass for ecg_id={ecg_id}")

        if superclass not in PTBXL_SUPERCLASS_TO_CANONICAL:
            raise ValueError(f"Unknown superclass '{superclass}'")

        canonical = PTBXL_SUPERCLASS_TO_CANONICAL[superclass]
        label_int = CANONICAL_TO_INT[canonical]

        # Build file path
        filename_lr = row.get("filename_lr", "")
        filename_hr = row.get("filename_hr", "")
        if self.sampling_rate == 500:
            rel_path = filename_hr
        else:
            rel_path = filename_lr

        if not rel_path:
            raise ValueError(f"No filename for ecg_id={ecg_id}")

        file_path = str(self.data_dir / rel_path)

        return PTBXLRecord(
            record_id=rel_path,
            participant_id=str(int(row.get("patient_id", 0))),
            ecg_id=int(ecg_id),
            sampling_rate=self.sampling_rate,
            n_samples=int(row.get("recording_date", 0)),  # placeholder; actual from wfdb
            n_leads=12,
            lead_names=self.LEAD_NAMES,
            label_raw=superclass,
            label_canonical=canonical,
            label_int=label_int,
            age=row.get("age", None),
            sex=row.get("sex", None),
            source_dataset="ptbxl",
            dataset_version="1.0.2",
            file_path=file_path,
            is_valid=True,
        )

    # ── Signal Loading ────────────────────────────────────────────────────────

    def load_signal(self, record: PTBXLRecord) -> Tuple[np.ndarray, int]:
        """
        Load the raw ECG signal for a record.

        Returns
        -------
        signal : np.ndarray, shape (n_samples,) for single lead
        fs : int, actual sampling rate from WFDB header
        """
        try:
            import wfdb
        except ImportError:
            raise ImportError("wfdb not installed. Run: pip install wfdb")

        wfdb_path = str(self.data_dir / record.record_id)
        try:
            wfdb_record = wfdb.rdrecord(wfdb_path)
        except Exception as exc:
            raise IOError(f"Cannot read WFDB record {wfdb_path}: {exc}")

        signals = wfdb_record.p_signal  # (n_samples, n_leads)
        fs = wfdb_record.fs

        if signals is None:
            raise ValueError(f"Null signal in {wfdb_path}")

        # Extract target lead
        lead_signal = signals[:, self._lead_idx]
        return lead_signal.astype(np.float32), fs

    def load_12lead_signal(self, record: PTBXLRecord) -> Tuple[np.ndarray, int]:
        """Load all 12 leads. Returns (n_samples, 12) array."""
        try:
            import wfdb
        except ImportError:
            raise ImportError("wfdb not installed.")

        wfdb_path = str(self.data_dir / record.record_id)
        wfdb_record = wfdb.rdrecord(wfdb_path)
        signals = wfdb_record.p_signal.astype(np.float32)  # (n_samples, 12)
        return signals, wfdb_record.fs

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self, max_records: Optional[int] = None) -> PTBXLValidationReport:
        """
        Run full dataset validation. Returns a PTBXLValidationReport.
        Does NOT silently discard records — every issue is logged.
        """
        records = self.load_all_records(max_records=max_records)
        report = PTBXLValidationReport()
        report.total_records = len(records)
        patient_ids = set()
        reason_counts: Dict[str, int] = {}

        for rec in records:
            patient_ids.add(rec.participant_id)
            sr = rec.sampling_rate
            report.sampling_rate_distribution[sr] = (
                report.sampling_rate_distribution.get(sr, 0) + 1
            )

            if not rec.is_valid:
                report.invalid_records += 1
                for note in rec.validation_notes:
                    reason_counts[note[:80]] = reason_counts.get(note[:80], 0) + 1
                continue

            # Signal-level validation (sample a subset for speed)
            try:
                signal, fs = self.load_signal(rec)
                self._validate_signal(signal, fs, rec, reason_counts, report)
            except Exception as exc:
                rec.is_valid = False
                rec.validation_notes.append(str(exc))
                report.invalid_records += 1
                reason_counts[f"Load error: {str(exc)[:60]}"] = (
                    reason_counts.get(f"Load error: {str(exc)[:60]}", 0) + 1
                )
                continue

            report.valid_records += 1
            if rec.label_canonical == "NORMAL":
                report.n_normal += 1
            elif rec.label_canonical == "ABNORMAL":
                report.n_abnormal += 1
            else:
                report.n_excluded += 1

        report.n_patients = len(patient_ids)
        report.invalid_reasons = reason_counts
        report.invalid_records = report.total_records - report.valid_records
        return report

    def _validate_signal(self, signal: np.ndarray, fs: int, rec: PTBXLRecord,
                          reason_counts: dict, report: PTBXLValidationReport):
        """Perform signal-level validation checks and update rec.is_valid."""
        issues = []
        if len(signal) == 0:
            issues.append("Empty signal")
        if not np.isfinite(signal).all():
            issues.append("NaN or Inf values")
        if np.std(signal) < 1e-6:
            issues.append("Flatline signal (std < 1e-6)")
        if fs not in (100, 500):
            issues.append(f"Unsupported sampling rate: {fs}")
        if len(signal) < fs * 3:
            issues.append(f"Signal too short: {len(signal)} samples")

        for issue in issues:
            rec.validation_notes.append(issue)
            reason_counts[issue] = reason_counts.get(issue, 0) + 1
        if issues:
            rec.is_valid = False

    # ── Manifest Generation ───────────────────────────────────────────────────

    def build_manifest(
        self,
        output_path: str = "data/manifests/ptbxl_manifest.csv",
        max_records: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Build a machine-readable CSV manifest of all valid records.
        Manifest is fully reproducible given the same dataset.

        Returns
        -------
        pd.DataFrame with one row per valid record.
        """
        records = self.load_all_records(max_records=max_records)
        valid = [r for r in records if r.is_valid]

        rows = []
        for r in valid:
            rows.append({
                "participant_id": r.participant_id,
                "ecg_id": r.ecg_id,
                "record_id": r.record_id,
                "source_dataset": r.source_dataset,
                "dataset_version": r.dataset_version,
                "file_path": r.file_path,
                "sampling_rate": r.sampling_rate,
                "lead": self.target_lead,
                "label_raw": r.label_raw,
                "label_canonical": r.label_canonical,
                "label_int": r.label_int,
                "age": r.age,
                "sex": r.sex,
                "preprocessing_version": self.preprocessing_version,
                "split": "",      # filled by generate_splits()
            })

        df = pd.DataFrame(rows)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Manifest saved: {output_path} ({len(df)} records)")
        return df

    def generate_splits(
        self,
        manifest_df: pd.DataFrame,
        val_fraction: float = 0.15,
        test_fraction: float = 0.15,
        seed: int = 42,
        output_path: str = "data/splits/ptbxl_splits.csv",
    ) -> pd.DataFrame:
        """
        Patient-level train/validation/test split.
        NEVER splits windows from the same patient across sets.

        Algorithm:
        1. Shuffle patient IDs (deterministically with seed).
        2. Assign patients to test (last test_fraction).
        3. Assign patients to val (next val_fraction).
        4. Remaining patients → train.

        Parameters
        ----------
        manifest_df : DataFrame from build_manifest()
        val_fraction, test_fraction : fractions of PATIENTS (not records)
        seed : random seed for deterministic splits
        output_path : where to save the annotated manifest

        Returns
        -------
        DataFrame with 'split' column filled in.
        """
        rng = np.random.RandomState(seed)
        patients = manifest_df["participant_id"].unique()
        patients = np.array(sorted(patients))  # sort first for determinism
        rng.shuffle(patients)

        n = len(patients)
        n_test = max(1, int(np.ceil(n * test_fraction)))
        n_val = max(1, int(np.ceil(n * val_fraction)))

        test_patients = set(patients[-n_test:])
        val_patients = set(patients[-(n_test + n_val):-n_test])
        train_patients = set(patients[:-(n_test + n_val)])

        # Assign splits
        def assign_split(pid):
            if pid in test_patients:
                return "test"
            elif pid in val_patients:
                return "val"
            else:
                return "train"

        manifest_df = manifest_df.copy()
        manifest_df["split"] = manifest_df["participant_id"].map(assign_split)

        # Log distribution
        split_counts = manifest_df["split"].value_counts()
        logger.info(f"Split distribution (records): {split_counts.to_dict()}")
        logger.info(f"Patients: train={len(train_patients)}, "
                    f"val={len(val_patients)}, test={len(test_patients)}")

        # Leakage check
        assert len(train_patients & val_patients) == 0, "LEAK: train ∩ val"
        assert len(train_patients & test_patients) == 0, "LEAK: train ∩ test"
        assert len(val_patients & test_patients) == 0, "LEAK: val ∩ test"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        manifest_df.to_csv(output_path, index=False)
        logger.info(f"Splits saved: {output_path}")
        return manifest_df

    # ── Convenience ───────────────────────────────────────────────────────────

    def get_split_records(
        self, manifest_df: pd.DataFrame, split: str
    ) -> pd.DataFrame:
        """Return manifest rows for a specific split."""
        return manifest_df[manifest_df["split"] == split].reset_index(drop=True)

    def print_validation_report(self, report: PTBXLValidationReport):
        """Pretty-print a validation report."""
        print("=" * 60)
        print("PTB-XL DATASET VALIDATION REPORT")
        print("=" * 60)
        print(f"Total records:    {report.total_records}")
        print(f"Valid records:    {report.valid_records}")
        print(f"Invalid records:  {report.invalid_records}")
        print(f"Unique patients:  {report.n_patients}")
        print(f"  NORMAL:         {report.n_normal}")
        print(f"  ABNORMAL:       {report.n_abnormal}")
        print(f"  Excluded:       {report.n_excluded}")
        print(f"\nSampling rates: {report.sampling_rate_distribution}")
        if report.invalid_reasons:
            print("\nInvalid reasons:")
            for reason, count in sorted(
                report.invalid_reasons.items(), key=lambda x: -x[1]
            ):
                print(f"  {count:4d} × {reason}")
        print("=" * 60)
