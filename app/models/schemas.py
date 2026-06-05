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
    eta: Optional[int]
    delegated_to: Optional[str] = None
    lamport_clock: int

    class Config:
        use_enum_values = True

class DriverRequest(BaseModel):
    name: str
    license_plate: str

class DriverResponse(BaseModel):
    id: str
    name: str
    license_plate: str
    available: bool

class DriverStats(BaseModel):
    total: int
    available: int
    busy: int