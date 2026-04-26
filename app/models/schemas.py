from pydantic import BaseModel
from typing import Optional
from app.models.ride import RideStatus

class RideRequest(BaseModel):
    origin: Optional[str]
    destination: Optional[str]
    passenger_id: Optional[str]

class RideResponse(BaseModel):
    id: str
    status: RideStatus
    origin: str
    destination: str
    passenger_id: str
    driver_id: Optional[str] = None
    valor: Optional[float] = None
    delegated_to: Optional[str] = None
    lamport_clock: int