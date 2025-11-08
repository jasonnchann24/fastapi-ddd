from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class DomainEvent:
    """
    Base type for all domain events.
    """

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def name(self) -> str:
        return self.__class__.__name__
