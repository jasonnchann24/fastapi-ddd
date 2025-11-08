import importlib
import punq
from typing import Type, TypeVar
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_ddd.core.config import INSTALLED_DOMAINS

container = punq.Container()


def register_event_bus(event_bus_instance) -> None:
    """
    Register the EventBus instance created in main.py.
    Must be called before any domain registrations that depend on EventBus.
    """
    from fastapi_ddd.core.events.event_bus import EventBus

    container.register(EventBus, instance=event_bus_instance)


for domain in INSTALLED_DOMAINS:
    try:
        mod = importlib.import_module(
            f"fastapi_ddd.domains.{domain}.container_registration"
        )
    except ModuleNotFoundError:
        print(f"⚠️ Domain {domain} has no container_registration module — skipped.")
        continue

    if hasattr(mod, "register"):
        mod.register(container)
    else:
        print(f"⚠️ Domain {domain} has no register() function — skipped.")

T = TypeVar("T")


def resolve_with_session(service_type: Type[T], session: AsyncSession) -> T:
    """
    Resolve a service from the container and ensure a SQLModel AsyncSession is provided.

    Strategy:
    1) Prefer constructor injection by passing `session` as a named argument to the
       container. punq propagates provided kwargs to dependencies that declare a
       parameter with the same name (e.g., `__init__(..., session: AsyncSession)`).
    2) As a safety net, perform light attribute injection for any already-constructed
       collaborators that expose a `session` attribute.
    """
    try:
        service = container.resolve(service_type, session=session)
    except TypeError:
        service = container.resolve(service_type)

    # Fallback attribute injection in case some collaborators are already built and
    # just need the session set.
    for _, attr_value in vars(service).items():
        if hasattr(attr_value, "session"):
            setattr(attr_value, "session", session)

    return service
