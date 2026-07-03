
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.ride import RideStatus


class RideModel(Base):
    __tablename__ = "rides"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    status: Mapped[str] = mapped_column(
        SAEnum(RideStatus, name="ridestatus"),
        nullable=False
    )

    #campos do location
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    origin_street: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_number: Mapped[str] = mapped_column(String(20), nullable=False)
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_state: Mapped[str] = mapped_column(String(2), nullable=False)

    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination_street: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_number: Mapped[str] = mapped_column(String(20), nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_state: Mapped[str] = mapped_column(String(2), nullable=False)

    passenger_id: Mapped[str] = mapped_column(String(255), nullable=False)
    driver_id: Mapped[str] = mapped_column(String(255), nullable=True)

    valor: Mapped[float] = mapped_column(Float, nullable=True)
    eta: Mapped[int] = mapped_column(Integer, default=0)
    delegated_to: Mapped[str] = mapped_column(String(255), nullable=True)
    core_ride_uuid: Mapped[str] = mapped_column(String(36), nullable=True)      
    delegation_winner: Mapped[str] = mapped_column(String(255), nullable=True)
    lamport_clock: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )