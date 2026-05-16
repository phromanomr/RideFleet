import random
import asyncio
from app.models.ride import Ride, RideStatus
from app.distributed.logical_clock import log_event
from app import state
from app.config import (
    MAX_DRIVERS,
    REJECTION_CHANCE,
    DELAY_MATCH_TO_CONFIRM,
    DELAY_CONFIRMED_TO_IN_TRANSIT,
    DELAY_IN_TRANSIT_TO_COMPLETED, MAX_QUEUE_SIZE,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ride_model import RideModel

def tem_motorista_disponivel() -> bool:
    return state.motoristas_ocupados < MAX_DRIVERS

def _motorista_aceitou() -> bool:
    return random.random() > REJECTION_CHANCE

async def solicitar_corrida(corrida: Ride) -> Ride:
    if tem_motorista_disponivel():
        print(f"TEM MOTORISTA DISPONIVEL")
        await _atribuir_motorista(corrida)
    elif len(state.fila) < MAX_QUEUE_SIZE:
        print(f"NÃO TEM MOTORISTA DISPONIVEL. Vamos por na fila")
        state.fila.append(corrida)
        await log_event(corrida.id, "ride_queued", {"queue_size": len(state.fila)})
    else:
        corrida_a_delegar = state.fila.popleft() #delega a primeira corrida da fila
        state.fila.append(corrida) #insere a nova corida na fila
        await log_event(corrida.id, "ride_queued", {"queue_size": len(state.fila)})
        await _delegar_ao_core(corrida_a_delegar)

    return corrida


async def _atribuir_motorista(corrida: Ride):
    if _motorista_aceitou():
        state.motoristas_ocupados += 1
        corrida.status = RideStatus.MATCH
        await log_event(corrida.id, "ride_matched", {"driver_accepted": True})
        print(f"corrida aceita: {corrida.id}")
        asyncio.ensure_future(_simular_corrida(corrida))
    else:
        state.fila.appendleft(corrida)
        await log_event(corrida.id, "ride_rejected", {"driver_accepted": False})
        print(f"corrida rejeitada")


async def _simular_corrida(corrida: Ride):

    await asyncio.sleep(DELAY_MATCH_TO_CONFIRM)
    corrida.status = RideStatus.CONFIRM
    await log_event(corrida.id, "ride_confirmed", {})

    await asyncio.sleep(DELAY_CONFIRMED_TO_IN_TRANSIT)
    corrida.status = RideStatus.IN_TRANSIT
    await log_event(corrida.id, "ride_in_transit", {})

    await asyncio.sleep(DELAY_IN_TRANSIT_TO_COMPLETED)
    corrida.status = RideStatus.COMPLETE
    state.motoristas_ocupados -= 1
    await log_event(corrida.id, "ride_completed", {})

    await _processar_fila()


async def _processar_fila():
    if not state.fila:
        return # fila vazia, nada a processar

    if not tem_motorista_disponivel():
        return

    corrida = state.fila.popleft()
    await _atribuir_motorista(corrida)

async def _delegar_ao_core(corrida: Ride):
    # Aqui você implementaria a lógica para enviar a corrida ao Core
    corrida.status = RideStatus.CANCELED
    await log_event(corrida.id, "ride_delegated_to_core", {})
    print(f"Corrida {corrida.id} delegada ao Core")

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
