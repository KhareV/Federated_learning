"""Prevent deferred scaffolding from becoming an accidental release feature."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_active_application_imports_only_centralized_routers():
    main = (ROOT / "backend/main.py").read_text()
    assert "from backend.api.routes import monitoring, system, websocket, inference, reports" in main
    for deferred in ("federated", "alerts", "devices", "experiments", "baseline", "signals", "anomaly"):
        assert f"include_router({deferred}.router)" not in main


def test_deferred_scaffolding_is_documented():
    document = (ROOT / "docs/DEFERRED_COMPONENTS.md").read_text()
    assert "not imported by `backend.main`" in document
    assert "must not be imported into an active router" in document
