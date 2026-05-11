from typing import Optional
from pydantic import BaseModel
from app.models.location import Location
from app.models.ride import RideStatus

class RideRequest(BaseModel):
    passenger_id: str
    origin: Location
    destination: Location

class RideResponse(BaseModel):
    id: str
    status: RideStatus
    origin: Location
    destination: Location
    passenger_id: str
    driver_id: Optional[str] = None
    valor: Optional[float] = None
    delegated_to: Optional[Location] = None
    lamport_clock: int

    class Config:
        use_enum_values = True