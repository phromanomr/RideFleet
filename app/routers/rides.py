from fastapi import APIRouter, HTTPException
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride
from app.distributed.logical_clock import log_event
from app.services.ride_service import solicitar_corrida
from app import state

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
        details={"origin": body.origin.city, "destination": body.destination.city}
    )
    corridas[corrida.id] = corrida
    print(f"Corrida solicitada: {corrida.id} - Passageiro: {corrida.passenger_id} - Origem: {corrida.origin.city} - Destino: {corrida.destination.city}")
    corrida = await solicitar_corrida(corrida)

    return corrida

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: str):
    corrida = corridas.get(ride_id)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não econtrada")
    return corrida