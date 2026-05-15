import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

class LamportClock:
    def __init__(self):
        self._clock = 0
        self._lock = asyncio.Lock()

    async def tick(self) -> int:
        async with self._lock:
            self._clock += 1
            return self._clock

    async def receive(self, remote_clock: int) -> int:
        async with self._lock:
            self._clock = max(self._clock, remote_clock) + 1
            return self._clock

    @property
    def value(self) -> int:
        return self._clock


lamport = LamportClock()

@dataclass
class AuditEvent:
    ride_id: str
    event_type: str
    service: str
    lamport_clock: int
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "ride_id": self.ride_id,
            "event_type": self.event_type,
            "service": self.service,
            "lamport_clock": self.lamport_clock,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }

_audit_log: list[AuditEvent] = []

async def log_event(ride_id: str, event_type: str, details: dict = None) -> int:
    clock = await lamport.tick()
    event = AuditEvent(
        ride_id=ride_id,
        event_type=event_type,
        service="vrumvrum",
        lamport_clock=clock,
        details=details,
    )
    _audit_log.append(event)
    return clock

def get_audit_log(ride_id: str) -> list[dict]:
    events = [e for e in _audit_log if e.ride_id == ride_id]
    events.sort(key=lambda e: e.lamport_clock)
    return [e.to_dict() for e in events]