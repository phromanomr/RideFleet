from fastapi import APIRouter
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.driver_model import DriverModel
from app import state, metrics
import os

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count())
            .select_from(DriverModel)
            .where(DriverModel.available == True)
        )
        motoristas_disponiveis = result.scalar()

    tamanho_fila = len(state.fila)

    latencia_media = metrics.calcular_latencia_media()

    taxa_erro = metrics.calcular_taxa_erro()

    alertas = []

    if tamanho_fila > 10:
        alertas.append("Fila de corridas acima do limite")

    if taxa_erro > 0.3:
        alertas.append("Taxa de erro elevada")

    status = "UP"

    if alertas:
        status = "DEGRADED"

    instance_id = os.getenv("INSTANCE_ID", "unknown")

    return {
        "instance_id": instance_id,
        "status": status,
        "motoristas_disponiveis": motoristas_disponiveis,
        "tamanho_fila": tamanho_fila,
        "latencia_media_ms": latencia_media,
        "taxa_erro": taxa_erro,
        "alertas": alertas
    }