from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

@dataclass
class Driver:
    name: str
    license_plate: str
    id: str = field(default_factory=lambda: str(uuid4()))
    available: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
