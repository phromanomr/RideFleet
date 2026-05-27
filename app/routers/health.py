from fastapi import APIRouter, Request
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.driver_model import DriverModel
from app.models.ride_model import RideModel
from app import metrics
from app.services.rabbitmq_service import obter_tamanho_fila
import os

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(request: Request):
    # 1. Motoristas disponíveis no banco
    motoristas_disponiveis = 0
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count())
                .select_from(DriverModel)
                .where(DriverModel.available == True)
            )
            motoristas_disponiveis = result.scalar() or 0
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 1b. Corridas agrupadas por status (para o Grafana)
    corridas_por_status = {}
    try:
        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(RideModel.status, func.count().label("total"))
                .group_by(RideModel.status)
            )
            for row in rows:
                corridas_por_status[row.status] = row.total
        metrics.atualizar_corridas_por_status(corridas_por_status)
    except Exception:
        pass  # não crítico, só afeta o Grafana

    # 2. Tamanho real da fila de entrada no RabbitMQ
    tamanho_fila = 0
    rabbitmq_status = "ok"
    try:
        tamanho_fila = await obter_tamanho_fila()
    except Exception as e:
        rabbitmq_status = f"error: {str(e)}"

    # Atualiza os gauges do Prometheus com os valores atuais
    metrics.atualizar_fila(tamanho_fila)
    metrics.atualizar_motoristas(motoristas_disponiveis)

    latencia_media = metrics.calcular_latencia_media()
    taxa_erro = metrics.calcular_taxa_erro()

    # 3. Alertas e status geral
    alertas = []
    if rabbitmq_status != "ok":
        alertas.append(f"RabbitMQ indisponível: {rabbitmq_status}")
    if db_status != "ok":
        alertas.append(f"Banco de dados indisponível: {db_status}")
    if tamanho_fila > 10:
        alertas.append("Fila de corridas acima do limite (>10)")
    if taxa_erro > 0.3:
        alertas.append("Taxa de erro elevada (>30%)")
    if motoristas_disponiveis == 0:
        alertas.append("Nenhum motorista disponível")

    # DOWN se infra crítica falhou, DEGRADED se só há alertas de negócio
    if rabbitmq_status != "ok" or db_status != "ok":
        status = "DOWN"
    elif alertas:
        status = "DEGRADED"
    else:
        status = "UP"

    instance_id = os.getenv("INSTANCE_ID", "unknown")
    return {
        "instance_id": instance_id,
        "status": status,
        "motoristas_disponiveis": motoristas_disponiveis,
        "tamanho_fila": tamanho_fila,
        "latencia_media_ms": latencia_media,
        "taxa_erro": taxa_erro,
        "alertas": alertas,
    }