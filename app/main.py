from fastapi import FastAPI
from app.routers import rides, audit, drivers

app = FastAPI(
    title="VrumVrum",
    description="Serviço de transporte distribuído -  SIN 142 UFV-CRP 2026/1",
    version="0.1.0",
)

app.include_router(rides.router)
app.include_router(audit.router)
app.include_router(drivers.router)
@app.get("/health")
def health():
    return {"status": "ok", "service": "vrumvrum"}


