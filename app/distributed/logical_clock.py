import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_model import AuditModel
from app.logging_config import log_estruturado

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

#mantém a lista em memoria como fallback
_audit_log: list[AuditEvent] = []

async def log_event(
    ride_id: str,
    event_type: str,
    details: dict = None,
    db: AsyncSession = None,
    estado_anterior: str = None,
    estado_novo: str = None,
) -> int:

    clock = await lamport.tick()
    event = AuditEvent(
        ride_id=ride_id,
        event_type=event_type,
        service="vrumvrum",
        lamport_clock=clock,
        details=details,
    )
    _audit_log.append(event)

    if db:
        audit_db = AuditModel(
            id=str(uuid.uuid4()),
            ride_id=ride_id,
            event_type=event_type,
            service="vrumvrum",
            lamport_clock=clock,
            estado_anterior=estado_anterior,
            estado_novo=estado_novo,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit_db)
        await db.commit()

    log_estruturado(
        evento=event_type,
        corrida_id=ride_id,
        estado_anterior=estado_anterior,
        estado_novo=estado_novo,
        lamport_clock=clock,
        extras=details,
    )
    return clock

async def get_audit_log_db(ride_id: str, db: AsyncSession) -> list[dict]:
    """Busca eventos do banco de dados."""
    result = await db.execute(
        select(AuditModel)
        .where(AuditModel.ride_id == ride_id)
        .order_by(AuditModel.lamport_clock)
    )
    events = result.scalars().all()
    return [
        {
            "ride_id": e.ride_id,
            "event_type": e.event_type,
            "service": e.service,
            "lamport_clock": e.lamport_clock,
            "estado_anterior": e.estado_anterior,
            "estado_novo": e.estado_novo,
            "timestamp": e.timestamp.isoformat(),
            "details": e.details,
        }
        for e in events
    ]

def get_audit_log(ride_id: str) -> list[dict]:
    events = [e for e in _audit_log if e.ride_id == ride_id]
    events.sort(key=lambda e: e.lamport_clock)
    return [e.to_dict() for e in events]