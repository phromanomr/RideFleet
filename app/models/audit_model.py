import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class AuditModel(Base):
    __tablename__ = "audit_events"

    #identificação
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    #campos principas
    ride_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False)

    #relogio de lamport
    lamport_clock: Mapped[int] = mapped_column(Integer, nullable=False)

    #estados
    estado_anterior: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado_novo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    #timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )