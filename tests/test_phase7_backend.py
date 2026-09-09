import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.database import create_all_tables
from backend.main import app
from preprocessing.ecg import synthesize_ecg_segment


@pytest.mark.asyncio
async def test_session_lifecycle_and_persisted_inference():
    await create_all_tables()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/monitoring/sessions/start", json={"subject_id": "S-1", "device_id": "D-1"})
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        samples = synthesize_ecg_segment(2500, seed=11).tolist()
        response = await client.post("/inference", json={"session_id": session_id, "samples": samples, "sampling_rate": 250, "source": "REPLAY"})
        assert response.status_code == 201
        body = response.json()
        assert body["model_version"] == "MODEL_V1"
        assert body["disclaimer"] == "Research prototype; not a medical diagnosis."
        history = await client.get(f"/monitoring/sessions/{session_id}/predictions")
        assert history.status_code == 200
        assert len(history.json()) == 1
        stopped = await client.put(f"/monitoring/sessions/{session_id}/stop")
        assert stopped.status_code == 200
        assert stopped.json()["status"] == "stopped"


@pytest.mark.asyncio
async def test_inference_rejects_unknown_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/inference", json={"session_id": "missing", "samples": [0.0]})
    assert response.status_code == 404
