from fastapi import APIRouter, HTTPException
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride
from app.distributed.logical_clock import lamport, log_event

router = APIRouter(prefix="/rides", tags=["rides"])

corridas = {} # armazenamento temporário em memória, substituir por BD depois

@router.post("/", response_model=RideResponse)
async def request_ride(body: RideRequest):
    corrida = Ride(
        origin=body.origin,
        destination=body.destination,
        passenger_id=body.passenger_id,
    )
    corrida.lamport_clock = await log_event(
        ride_id=corrida.id,
        event_type="ride_requested",
        details={"origin": body.origin, "destination": body.destination}
    )
    corridas[corrida.id] = corrida
    return corrida

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: str):
    corrida = corridas.get(ride_id)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não econtrada")
    return corrida