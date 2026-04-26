from fastapi import APIRouter, HTTPException
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride

router = APIRouter(prefix="/rides", tags=["rides"])

corridas = {} # armazenamento temporário em memória, substituir por BD depois

@router.post("/", response_model=RideResponse)
def request_ride(body: RideRequest):
    corrida = Ride(
        origin=body.origin,
        destination=body.destination,
        passenger_id=body.passenger_id,
    )
    corridas[corrida.id] = corrida
    return corrida

@router.get("/{ride_id}", response_model=RideResponse)
def get_ride(ride_id: str):
    corrida = corridas.get(ride_id)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não econtrada")
    return corrida