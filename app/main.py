from fastapi import FastAPI

app = FastAPI(
    title="VrumVrum",
    description="Serviço de transporte distribuído -  SIN 142 UFV-CRP 2026/1",
    version="0.1.0",
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "vrumvrum"}


