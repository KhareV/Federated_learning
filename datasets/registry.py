"""Dataset registry and read-only inventory checks for NHM.

This module does not load signal samples or alter raw data. It verifies that
the supplied dataset roots have the expected metadata and paired files before
the training pipelines are run.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Dict, Iterable, Mapping

import yaml


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    display_name: str
    version: str
    root: Path
    source: str
    role: str
    config: Mapping[str, Any]

    def to_dict(self, project_root: Path) -> Dict[str, Any]:
        data = dict(asdict(self))
        data["root"] = str(self.root.relative_to(project_root))
        data["config"] = dict(self.config)
        return data


def load_registry(path: str | Path = "configs/datasets.yaml", project_root: str | Path = ".") -> Dict[str, DatasetSpec]:
    project_root = Path(project_root).resolve()
    with Path(path).open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle) or {}

    result: Dict[str, DatasetSpec] = {}
    for name, config in (document.get("datasets") or {}).items():
        root = Path(config["root"])
        if not root.is_absolute():
            root = project_root / root
        result[name] = DatasetSpec(
            name=name,
            display_name=config.get("display_name", name),
            version=str(config["version"]),
            root=root.resolve(),
            source=config.get("source", "unknown"),
            role=config.get("role", "unspecified"),
            config=config,
        )
    return result


def _paired_stems(root: Path, extension_a: str, extension_b: str) -> tuple[set[str], set[str]]:
    first = {p.stem for p in root.glob(f"*.{extension_a}")}
    second = {p.stem for p in root.glob(f"*.{extension_b}")}
    return first, second


def inspect_dataset(spec: DatasetSpec) -> Dict[str, Any]:
    """Return a JSON-serializable inventory and validation result."""
    root = spec.root
    root_display = str(spec.config.get("root", root))
    checks: list[str] = []
    errors: list[str] = []
    counts: Dict[str, int] = {}

    if not root.is_dir():
        return {"name": spec.name, "version": spec.version, "root": root_display, "status": "missing", "counts": {}, "checks": [], "errors": ["Dataset root does not exist"]}

    if spec.name == "ptbxl":
        metadata = root / "ptbxl_database.csv"
        statements = root / "scp_statements.csv"
        if metadata.is_file(): checks.append("ptbxl_database.csv present")
        else: errors.append("Missing ptbxl_database.csv")
        if statements.is_file(): checks.append("scp_statements.csv present")
        else: errors.append("Missing scp_statements.csv")
        for rate in (100, 500):
            headers = list((root / f"records{rate}").rglob("*.hea"))
            dat = list((root / f"records{rate}").rglob("*.dat"))
            counts[f"records{rate}_headers"] = len(headers)
            counts[f"records{rate}_dat"] = len(dat)
            if len(headers) != len(dat): errors.append(f"records{rate}: header/data count mismatch")
            elif headers: checks.append(f"records{rate}: paired WFDB files")
            else: errors.append(f"records{rate}: no WFDB records found")
        if metadata.is_file():
            with metadata.open("r", encoding="utf-8") as handle:
                counts["metadata_rows"] = max(0, sum(1 for _ in handle) - 1)
            if counts["metadata_rows"] != counts.get("records500_headers", -1):
                errors.append("PTB-XL metadata row count differs from records500")

    elif spec.name == "mitbih":
        dat, hea = _paired_stems(root, "dat", "hea")
        atr = {p.stem for p in root.glob("*.atr")}
        counts.update({"records_dat": len(dat), "records_headers": len(hea), "records_annotations": len(atr)})
        if dat == hea == atr and dat:
            checks.append("all MIT-BIH records have dat/hea/atr files")
        else:
            errors.append("MIT-BIH dat/hea/atr file stems are not identical")

    elif spec.name == "mitbih_noise_stress":
        files = list(root.glob("*.mat"))
        counts["mat_files"] = len(files)
        pattern = re.compile(r"e(?P<snr>-?\d+)$")
        snrs = []
        for file in files:
            match = pattern.search(file.stem)
            if match: snrs.append(int(match.group("snr")))
        counts["recognized_snr_files"] = len(snrs)
        counts["recognized_snr_levels"] = len(set(snrs))
        expected = set(spec.config.get("snr_levels_db", []))
        if files and expected.issubset(set(snrs)):
            checks.append("noise MAT files cover configured SNR levels")
        else:
            errors.append("noise MAT files do not cover all configured SNR levels")

    elif spec.name == "bidmc":
        headers = list(root.glob("*.hea"))
        dat = list(root.glob("*.dat"))
        csv_root = root / str(spec.config.get("csv_export_root", "bidmc_csv"))
        signal_csv = list(csv_root.glob("*_Signals.csv")) if csv_root.is_dir() else []
        numeric_csv = list(csv_root.glob("*_Numerics.csv")) if csv_root.is_dir() else []
        counts.update({"wfdb_headers": len(headers), "wfdb_dat": len(dat), "signal_csv": len(signal_csv), "numeric_csv": len(numeric_csv)})
        if headers and dat: checks.append("BIDMC WFDB files present")
        else: errors.append("BIDMC WFDB files are incomplete")
        if signal_csv and numeric_csv: checks.append("BIDMC CSV signal/numeric exports present")
        else: errors.append("BIDMC CSV exports are incomplete")

    status = "valid" if not errors else "invalid"
    return {"name": spec.name, "display_name": spec.display_name, "version": spec.version, "root": root_display, "role": spec.role, "status": status, "counts": counts, "checks": checks, "errors": errors}


def inventory(registry: Mapping[str, DatasetSpec]) -> Dict[str, Any]:
    reports = [inspect_dataset(spec) for spec in registry.values()]
    return {"registry_version": "1.0.0", "datasets": reports, "status": "valid" if all(r["status"] == "valid" for r in reports) else "invalid"}
