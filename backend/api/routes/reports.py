"""Read-only catalog for committed centralized research evidence."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/reports", tags=["reports"])

ROOT = Path(__file__).resolve().parents[3]
REPORTS = {
	"label-contract-audit": ("Label contract audit", ROOT / "experiments/label_audit_v1/label_contract_audit.json"),
	"external-gate-audit": ("External release gate audit", ROOT / "docs/EXTERNAL_GATE_AUDIT.md"),
	"ptbxl-baselines": ("PTB-XL baseline report", ROOT / "docs/PHASE3_REAL_PTBXL_BASELINES.md"),
	"calibration-external-noise": ("Calibration, external validation, and noise", ROOT / "docs/PHASE4_CALIBRATION_EXTERNAL_NOISE_REPORT.md"),
	"multimodal-status": ("Multimodal status", ROOT / "docs/PHASE5_MULTIMODAL_SIGNAL_REPORT.md")
}


@router.get("")
def reports():
	return [{"id": report_id, "title": title, "available": path.exists(), "format": path.suffix.lstrip(".")} for report_id, (title, path) in REPORTS.items()]


@router.get("/{report_id}")
def report(report_id: str):
	if report_id not in REPORTS:
		raise HTTPException(404, "Report not found")
	title, path = REPORTS[report_id]
	if not path.exists():
		raise HTTPException(404, "Report artifact unavailable")
	return {"id": report_id, "title": title, "format": path.suffix.lstrip("."), "content": path.read_text()}
