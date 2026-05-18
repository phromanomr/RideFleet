# app/services/ride_service.py

import random
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ride_model import RideModel

from app.models.ride import Ride, RideStatus
from app.models.driver_model import DriverModel
from app.distributed.logical_clock import log_event
from app.database import AsyncSessionLocal
from app import state
from app.config import (
    MAX_QUEUE_SIZE,
    REJECTION_CHANCE,
    DELAY_MATCH_TO_CONFIRM,
    DELAY_CONFIRMED_TO_IN_TRANSIT,
    DELAY_IN_TRANSIT_TO_COMPLETED,
)


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


def _motorista_aceitou() -> bool:
    return random.random() > REJECTION_CHANCE


async def solicitar_corrida(corrida: Ride) -> Ride:
    if await tem_motorista_disponivel():
        await _atribuir_motorista(corrida)
    elif len(state.fila) < MAX_QUEUE_SIZE:
        state.fila.append(corrida)
        await log_event(corrida.id, "ride_queued", {"queue_size": len(state.fila)})
    else:
        corrida_a_delegar = state.fila.popleft()
        state.fila.append(corrida)
        await log_event(corrida.id, "ride_queued", {"queue_size": len(state.fila)})
        await _delegar_ao_core(corrida_a_delegar)
    return corrida


async def _atribuir_motorista(corrida: Ride):
    motorista = await _buscar_motorista_disponivel()
    if not motorista:
        # motorista sumiu entre a verificação e a atribuição — enfileira
        state.fila.append(corrida)
        await log_event(corrida.id, "ride_queued", {"queue_size": len(state.fila)})
        return
    if _motorista_aceitou():
        await _ocupar_motorista(motorista.id)
        corrida.status = RideStatus.MATCH
        corrida.driver_id = motorista.id
        await log_event(corrida.id, "ride_matched", {"driver_id": motorista.id})
        await atualizar_corrida(corrida)  # ← adiciona aqui
        asyncio.ensure_future(_simular_corrida(corrida, motorista.id))
    else:
        state.fila.appendleft(corrida)
        await log_event(corrida.id, "ride_rejected_by_driver", {"driver_id": motorista.id})


async def _simular_corrida(corrida: Ride, driver_id: str):
    """Simula as transições de estado em background."""
    await asyncio.sleep(DELAY_MATCH_TO_CONFIRM)
    corrida.status = RideStatus.CONFIRM
    await atualizar_corrida(corrida)
    await log_event(corrida.id, "ride_confirmed", {"driver_id": driver_id})

    await asyncio.sleep(DELAY_CONFIRMED_TO_IN_TRANSIT)
    corrida.status = RideStatus.IN_TRANSIT
    await atualizar_corrida(corrida)
    await log_event(corrida.id, "ride_in_transit", {"driver_id": driver_id})

    await asyncio.sleep(DELAY_IN_TRANSIT_TO_COMPLETED)
    corrida.status = RideStatus.COMPLETE
    await atualizar_corrida(corrida)
    await log_event(corrida.id, "ride_completed", {"driver_id": driver_id})
    await _liberar_motorista(driver_id)
    await _processar_fila()


async def _processar_fila():
    if not state.fila:
        return
    if not await tem_motorista_disponivel():
        return
    corrida = state.fila.popleft()
    await _atribuir_motorista(corrida)


async def _delegar_ao_core(corrida: Ride):
    """
    Placeholder — será implementado na Semana 3.
    TODO:
      - Chamar POST /rides no Core com o JSON de delegação
      - Iniciar polling em background em GET /rides/{id}/status
      - Atualizar o status da nossa corrida conforme o Core responder
      - Manter a corrida no state.corridas para o passageiro acompanhar
    """
    corrida.status = RideStatus.CANCELED
    await log_event(corrida.id, "ride_delegated_to_core", {"reason": "queue_full"})


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
            ride_db.lamport_clock = corrida.lamport_clock
            await db.commit()