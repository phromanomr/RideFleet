from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class DriverModel(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_plate: Mapped[str] = mapped_column(String(8), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

