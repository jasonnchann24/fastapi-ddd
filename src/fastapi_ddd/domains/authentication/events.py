from dataclasses import dataclass
from fastapi_ddd.core.events.base import DomainEvent
from fastapi_ddd.core.events.contracts import UserSavedIntegrationEvent


@dataclass(kw_only=True)
class UserSavedEvent(DomainEvent):
    user_id: str
    username: str
    email: str

    def to_integration(self) -> UserSavedIntegrationEvent:
        return UserSavedIntegrationEvent(
            user_id=self.user_id, username=self.username, email=self.email
        )
