from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride
from app.distributed.logical_clock import log_event
from app.services.ride_service import (
    solicitar_corrida,
    salvar_corrida,
    buscar_corrida,
    listar_corridas,
    listar_corridas_em_andamento,
    buscar_status_corrida,
    ride_to_response
)

router = APIRouter(prefix="/rides", tags=["rides"])


@router.post("/", response_model=RideResponse)
async def request_ride(body: RideRequest, db: AsyncSession = Depends(get_db)):
    corrida = Ride(
        origin=body.origin,
        destination=body.destination,
        passenger_id=body.passenger_id,
    )
    corrida.lamport_clock = await log_event(
        ride_id=corrida.id,
        event_type="ride_requested",
        details={"origin": body.origin.city, "destination": body.destination.city},
        db=db,
        estado_anterior=None,
        estado_novo="request"
    )

    await salvar_corrida(corrida, db)
    await solicitar_corrida(corrida)

    return corrida

@router.get("/all", response_model=List[RideResponse])
async def get_all_rides(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rides_db = await listar_corridas(db, status=status)
    return [ride_to_response(r) for r in rides_db]

@router.get("/ongoing", response_model=List[RideResponse])
async def get_ongoing_rides(db: AsyncSession = Depends(get_db)):
    rides_db = await listar_corridas_em_andamento(db)
    return [ride_to_response(r) for r in rides_db]

@router.get("/{ride_id}/status")
async def get_status(ride_id: str, db: AsyncSession = Depends(get_db)):
    status = await buscar_status_corrida(ride_id, db)
    if status is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return {"id": ride_id, "status": status}

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: str, db: AsyncSession = Depends(get_db)):
    corrida = await buscar_corrida(ride_id, db)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return ride_to_response(corrida)

@router.get("/{ride_id}/delegation")
async def get_delegation_info(ride_id: str, db: AsyncSession = Depends(get_db)):
    corrida = await buscar_corrida(ride_id, db)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return {
        "id": ride_id,
        "core_ride_uuid": corrida.core_ride_uuid,
        "delegation_winner": corrida.delegation_winner,
    }