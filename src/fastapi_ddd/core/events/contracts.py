from dataclasses import dataclass

@dataclass(frozen=True)
class UserSavedIntegrationEvent:
    user_id: str
    username: str
    email: str
