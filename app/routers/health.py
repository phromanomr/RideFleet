from fastapi import APIRouter, Request
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.driver_model import DriverModel
from app import metrics  # Removemos o "state" daqui
from app.services.rabbitmq_service import obter_tamanho_fila  # Importamos o serviço da fila
import os

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(request: Request):
    # 1. Checa motoristas no banco
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.count())
            .select_from(DriverModel)
            .where(DriverModel.available == True)
        )
        motoristas_disponiveis = result.scalar()

    app_instance = request.app
    
    # 2. Busca o tamanho real da fila de entrada no RabbitMQ (Assíncrono)
    tamanho_fila = await obter_tamanho_fila()

    # 3. Métricas locais
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