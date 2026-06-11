# app/services/ride_service.py

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.distributed.logical_clock import lamport
from app.models.ride_model import RideModel
from app.models.ride import Ride, RideStatus
from app.models.location import Location
from app.models.driver_model import DriverModel
from app.distributed.logical_clock import log_event
from app.database import AsyncSessionLocal
from app import metrics
from app.services.rabbitmq_service import publicar_corrida_entrada, publicar_corrida_saida, obter_tamanho_fila
from app.services.core_service import solicitar_delegacao_core
from app.services.geo_service import calcular_preco, calcular_rota
from app.config import (
    MAX_QUEUE_SIZE,
    DELAY_MATCH_TO_CONFIRM,
    DELAY_CONFIRMED_TO_IN_TRANSIT,
    DELAY_IN_TRANSIT_TO_COMPLETED,
)
from app.logging_config import log_estruturado, get_logger
logger = get_logger()

# Lock global de verificação de tamanho de fila. Isso evita que o limite da fila interna seja ultrapassado
request_lock = asyncio.Lock()

async def _buscar_motorista_disponivel() -> DriverModel | None:
    """Busca um motorista disponível no banco."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DriverModel).where(DriverModel.available == True).limit(1)
        )
        return result.scalar_one_or_none()


async def tem_motorista_disponivel() -> bool:
    motorista = await _buscar_motorista_disponivel()
    return motorista is not None


async def _ocupar_motorista(driver_id: str):
    """Marca o motorista como ocupado no banco."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DriverModel).where(DriverModel.id == driver_id)
        )
        motorista = result.scalar_one_or_none()
        if motorista:
            motorista.available = False
            await db.commit()


async def _liberar_motorista(driver_id: str):
    """Marca o motorista como disponível no banco."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DriverModel).where(DriverModel.id == driver_id)
        )
        motorista = result.scalar_one_or_none()
        if motorista:
            motorista.available = True
            await db.commit()


async def solicitar_corrida(corrida: Ride) -> Ride:
    # Inicia monitoramento da corrida
    metrics.registrar_inicio_corrida(corrida.id)
    tamanho_fila = await obter_tamanho_fila()

    rota = await calcular_rota(
        {"lat": corrida.origin.lat, "lng": corrida.origin.lng}, 
        {"lat": corrida.destination.lat, "lng": corrida.destination.lng}
    )
    
    if rota is not None:
        corrida.eta = int(rota["duracao_s"])
        corrida.valor = calcular_preco(rota["distancia_km"])
    else:
        print("Aviso: Falha ao calcular rota. Usando valores padrão.")
        corrida.eta = 0
        corrida.valor = 12.50 # Ou seu PRECO_BASE

    # Prepara o dicionário para caso precise ir pra fila (RabbitMQ)
    corrida_dict = {
        "id": corrida.id,
        "origin": corrida.origin.model_dump() if hasattr(corrida.origin, 'model_dump') else corrida.origin.dict(),
        "destination": corrida.destination.model_dump() if hasattr(corrida.destination, 'model_dump') else corrida.destination.dict(),
        "passenger_id": corrida.passenger_id,
        "status": corrida.status.value,
        "driver_id": corrida.driver_id,
        "valor": corrida.valor,
        "eta": corrida.eta,
        "delegated_to": corrida.delegated_to,
        "lamport_clock": corrida.lamport_clock,
    }

    await atualizar_corrida(corrida)

    # Verifica/Atribui o lock a uma solicitação de corrida
    async with request_lock:
        tamanho_fila = await obter_tamanho_fila()

    if await tem_motorista_disponivel() and tamanho_fila == 0:
        log_estruturado("motorista_disponível", corrida_id=corrida.id, estado_novo="match")
        await _atribuir_motorista(corrida)
    elif tamanho_fila < MAX_QUEUE_SIZE:
        log_estruturado("corrida_enfileirada", corrida_id=corrida.id,
                        extras={"queue_size": tamanho_fila + 1})
        await publicar_corrida_entrada(corrida_dict)
        await log_event(corrida.id, "ride_queued", {"queue_size": tamanho_fila + 1})
    else:
        log_estruturado("overflow_delegado_ao_core", corrida_id=corrida.id,
                        nivel="WARN", extras={"queue_size": tamanho_fila})
        await publicar_corrida_saida(corrida_dict)
        await log_event(corrida.id, "overflow_reached_queued_for_delegation", {"queue_size": tamanho_fila})

    return corrida


async def processar_corrida_da_fila(corrida_dict: dict) -> bool:
    """
    Worker chamado pelo consumidor do RabbitMQ na fila de entrada.
    """
    if not await tem_motorista_disponivel():
        return False

    # Recria o objeto dataclass Ride
    corrida = Ride(
        id=corrida_dict["id"],
        origin=Location(**corrida_dict["origin"]),
        destination=Location(**corrida_dict["destination"]),
        passenger_id=corrida_dict["passenger_id"],
        status=RideStatus(corrida_dict["status"]),
        driver_id=corrida_dict.get("driver_id"),
        valor=corrida_dict.get("valor"),
        eta=corrida_dict.get("eta"),
        delegated_to=corrida_dict.get("delegated_to"),
        lamport_clock=corrida_dict.get("lamport_clock", 0)
    )

    sucesso = await _atribuir_motorista(corrida)
    return sucesso

async def processar_corrida_saida(corrida_dict: dict) -> bool:
    try:
        clock = await lamport.tick()
        await solicitar_delegacao_core(corrida_dict, clock)
        return True
    except Exception as e:
        logger.error("erro_ao_delegar_ao_core", erro=str(e))
        return False

async def _atribuir_motorista(corrida: Ride) -> bool:
    motorista = await _buscar_motorista_disponivel()
    if not motorista:
        log_estruturado("motorista_nao_encontrado", corrida_id=corrida.id, nivel="WARN")
        return False

    await _ocupar_motorista(motorista.id)
    corrida.status = RideStatus.MATCH
    corrida.driver_id = motorista.id
    log_estruturado("motorista_atribuido", corrida_id=corrida.id,
                    estado_anterior="request", estado_novo="match",
                    extras={"driver_id": motorista.id})
    await log_event(corrida.id, "ride_matched", {"driver_id": motorista.id})
    await atualizar_corrida(corrida)
    asyncio.ensure_future(_simular_corrida(corrida, motorista.id))
    return True


async def _simular_corrida(corrida: Ride, driver_id: str):
    """Simula as transições de estado em background."""
    await asyncio.sleep(DELAY_MATCH_TO_CONFIRM)
    corrida.status = RideStatus.CONFIRM
    await atualizar_corrida(corrida)
    log_estruturado("corrida_confirmada", corrida_id=corrida.id,
                    estado_anterior="match", estado_novo="confirm",
                    extras={"driver_id": driver_id})
    await log_event(corrida.id, "ride_confirmed", {"driver_id": driver_id})

    await asyncio.sleep(DELAY_CONFIRMED_TO_IN_TRANSIT)
    corrida.status = RideStatus.IN_TRANSIT
    await atualizar_corrida(corrida)
    log_estruturado("corrida_em_transito", corrida_id=corrida.id,
                    estado_anterior="confirm", estado_novo="in_transit",
                    extras={"driver_id": driver_id})
    await log_event(corrida.id, "ride_in_transit", {"driver_id": driver_id})

    await asyncio.sleep(DELAY_IN_TRANSIT_TO_COMPLETED)
    corrida.status = RideStatus.COMPLETE
    await atualizar_corrida(corrida)
    log_estruturado("corrida_concluida", corrida_id=corrida.id,
                    estado_anterior="in_transit", estado_novo="complete",
                    extras={"driver_id": driver_id})
    await log_event(corrida.id, "ride_completed", {"driver_id": driver_id})

    # Atualiza métricas de monitoramento
    metrics.registrar_fim_corrida(corrida.id)
    metrics.registrar_sucesso()
    await _liberar_motorista(driver_id)
    # Obs: não chamamos mais _processar_fila() aqui pois o RabbitMQ faz esse gerenciamento de concorrência.


async def salvar_corrida(corrida: Ride, db: AsyncSession) -> RideModel:
    """Converte o dataclass Ride para RideModel e salva no banco."""
    ride_db = RideModel(
        id=corrida.id,
        status=corrida.status,
        origin_lat=corrida.origin.lat,
        origin_lng=corrida.origin.lng,
        origin_street=corrida.origin.street,
        origin_number=corrida.origin.number,
        origin_city=corrida.origin.city,
        origin_state=corrida.origin.state,
        destination_lat=corrida.destination.lat,
        destination_lng=corrida.destination.lng,
        destination_street=corrida.destination.street,
        destination_number=corrida.destination.number,
        destination_city=corrida.destination.city,
        destination_state=corrida.destination.state,
        passenger_id=corrida.passenger_id,
        driver_id=corrida.driver_id,
        valor=corrida.valor,
        eta=corrida.eta,
        delegated_to=corrida.delegated_to,
        lamport_clock=corrida.lamport_clock,
    )
    db.add(ride_db)
    await db.commit()
    await db.refresh(ride_db)
    return ride_db


async def buscar_corrida(ride_id: str, db: AsyncSession) -> RideModel | None:
    """Busca uma corrida pelo id no banco."""
    result = await db.execute(
        select(RideModel).where(RideModel.id == ride_id)
    )
    return result.scalar_one_or_none()


async def atualizar_corrida(corrida: Ride) -> None:
    """Persiste as mudanças de status e driver_id da corrida no banco."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RideModel).where(RideModel.id == corrida.id)
        )
        ride_db = result.scalar_one_or_none()
        if ride_db:
            ride_db.status = corrida.status
            ride_db.driver_id = corrida.driver_id
            ride_db.valor = corrida.valor
            ride_db.eta = corrida.eta
            ride_db.lamport_clock = corrida.lamport_clock
            await db.commit()

async def buscar_status_corrida(ride_id: str, db: AsyncSession) -> RideModel | None:
    """Busca o status de uma corrida pelo id no banco. Usado para o endpoint de consulta de status."""
    result = await db.execute(select(RideModel.status).where(RideModel.id == ride_id))
    status = result.scalar_one_or_none()
    return status

async def listar_corridas(db: AsyncSession, status: str | None = None) -> list[RideModel]:
    """
    Retorna todas as corridas. Não aceita mais `passenger_id` — o endpoint retorna
    todas as corridas opcionamente filtradas por `status`.
    """
    q = select(RideModel)
    if status:
        # converte string para enum se precisar
        try:
            q = q.where(RideModel.status == RideStatus(status))
            log_estruturado("filtro_status_aplicado", extras={"status": status})
        except Exception:
            # se o status for invalido, retorna vazio
            log_estruturado("filtro_status_invalido", nivel="WARN", extras={"status": status})
            return []
    result = await db.execute(q)
    return result.scalars().all()

async def listar_corridas_em_andamento(db: AsyncSession) -> list[RideModel]:
    in_progress = [RideStatus.MATCH, RideStatus.CONFIRM, RideStatus.IN_TRANSIT]
    q = select(RideModel).where(RideModel.status.in_(in_progress))
    result = await db.execute(q)
    return result.scalars().all()

def ride_to_response(ride_model: RideModel) -> dict:
    """Converte um RideModel para um dicionário compatível com RideResponse."""
    return {
        "id": ride_model.id,
        "status": ride_model.status,
        "passenger_id": ride_model.passenger_id,
        "driver_id": ride_model.driver_id,
        "valor": ride_model.valor,
        "eta": ride_model.eta,
        "delegated_to": ride_model.delegated_to,
        "lamport_clock": ride_model.lamport_clock,
        "origin": {
            "lat": ride_model.origin_lat,
            "lng": ride_model.origin_lng,
            "street": ride_model.origin_street,
            "number": ride_model.origin_number,
            "city": ride_model.origin_city,
            "state": ride_model.origin_state
        },
        "destination": {
            "lat": ride_model.destination_lat,
            "lng": ride_model.destination_lng,
            "street": ride_model.destination_street,
            "number": ride_model.destination_number,
            "city": ride_model.destination_city,
            "state": ride_model.destination_state
        }
    }

async def receber_corrida_delegada(
    ride_uuid: str,
    origin: dict,
    destination: dict,
    passenger_id: str,
    origin_service_id: str,
    lamport_clock: int,
    db: AsyncSession
) -> Ride:
    """
    Processa uma corrida recebida por delegação do Core.
    Cria a corrida no banco, atribui motorista e inicia a simulação.
    """
    corrida = Ride(
        id=ride_uuid,
        origin=Location(**origin),
        destination=Location(**destination),
        passenger_id=passenger_id,
        status=RideStatus.MATCH,
        delegated_to=origin_service_id,
        lamport_clock=lamport_clock,
    )

    await salvar_corrida(corrida, db)
    await log_event(ride_uuid, "ride_received_from_core", {
        "origin_service": origin_service_id
    })

    asyncio.ensure_future(_atribuir_motorista(corrida))

    return corrida

