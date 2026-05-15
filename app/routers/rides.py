
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride
from app.distributed.logical_clock import log_event
from app.services.ride_service import solicitar_corrida, salvar_corrida, buscar_corrida

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
        details={"origin": body.origin.city, "destination": body.destination.city}
    )

    await salvar_corrida(corrida, db)
    await solicitar_corrida(corrida)

    return corrida

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: str, db: AsyncSession = Depends(get_db)):
    corrida = await buscar_corrida(ride_id, db)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return corrida