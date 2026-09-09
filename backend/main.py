from fastapi import FastAPI
from backend.api.routes import monitoring, system, websocket, inference, reports
from backend.db.database import create_all_tables
import asyncio

app = FastAPI(
    title="NHM Centralized ECG Monitor API",
    description="Medical disclaimer: This software is for research purposes only."
)

app.include_router(monitoring.router)
app.include_router(system.router)
app.include_router(reports.router)
app.include_router(websocket.router)
app.include_router(inference.router)

@app.on_event("startup")
async def startup():
    await create_all_tables()
    from backend.services.model_service import model_service, ModelUnavailable
    try:
        model_service.load()
    except ModelUnavailable:
        # API remains available for health/diagnostics when artifacts are absent.
        pass
