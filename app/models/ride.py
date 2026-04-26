from enum import Enum
import uuid
from datetime import datetime

class RideStatus(str, Enum):
    REQUESTED = "requested"
    MATCH = "match"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELED = "canceled"

class Ride:
    def __init__(
            self,
            origin: str,
            destination: str,
            passenger_id: str,
    ):
        self.id = str(uuid.uuid4())
        self.status = RideStatus.REQUESTED
        self.origin = origin
        self.destination = destination
        self.passenger_id = passenger_id
        self.driver_id = None
        self.valor = None
        self.delegated_to= None
        self.lamport_clock = 0
        self.created_at = datetime.utcnow()