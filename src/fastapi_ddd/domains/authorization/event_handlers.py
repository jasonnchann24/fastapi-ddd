from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_ddd.core.events.contracts import UserSavedIntegrationEvent
from fastapi_ddd.core.events.event_bus import EventBus
from fastapi_ddd.core.containers import resolve_with_session
from .services import RoleService


async def assign_default_roles(
    event: UserSavedIntegrationEvent, session: AsyncSession | None
):
    """Assign default 'user' role to newly registered users"""
    if session is None:
        return

    service = resolve_with_session(RoleService, session)

    roles = await service.repository.get_by_names(["user"])

    if not roles:
        print("⚠️ Default role 'user' not found. Skipping role assignment.")
        return

    role_ids = [r.id for r in roles]
    await service.sync_user_to_roles(user_id=event.user_id, role_ids=role_ids)


def register_event_handlers(bus: EventBus) -> None:
    bus.subscribe(UserSavedIntegrationEvent, assign_default_roles)
