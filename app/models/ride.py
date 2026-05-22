from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
from app.models.location import Location

class RideStatus(str, Enum):
    REQUEST = "REQUEST"
    MATCH = "MATCH"
    CONFIRM = "CONFIRM"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETE = "COMPLETE"
    CANCELED = "CANCELED"


@dataclass
class Ride:
    origin: Location
    destination: Location
    passenger_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: RideStatus = RideStatus.REQUEST
    driver_id: str | None = None
    valor: float | None = None
    delegated_to: str | None = None
    lamport_clock: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)