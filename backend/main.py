from fastapi import FastAPI
from backend.api.routes import monitoring, signals, anomaly, baseline, federated, experiments, devices, alerts, reports, system, websocket
from backend.db.database import create_all_tables
import asyncio

app = FastAPI(
    title="QAPFL Health Monitor API",
    description="Medical disclaimer: This software is for research purposes only."
)

app.include_router(monitoring.router)
app.include_router(signals.router)
app.include_router(anomaly.router)
app.include_router(baseline.router)
app.include_router(federated.router)
app.include_router(experiments.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(system.router)
app.include_router(websocket.router)

@app.on_event("startup")
async def startup():
    await create_all_tables()
