import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_reports_catalog_contains_external_gate_audit():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		catalog = await client.get("/reports")
		assert catalog.status_code == 200
		assert any(item["id"] == "external-gate-audit" and item["available"] for item in catalog.json())
		report = await client.get("/reports/external-gate-audit")
		assert report.status_code == 200
		assert "fails" in report.json()["content"]
