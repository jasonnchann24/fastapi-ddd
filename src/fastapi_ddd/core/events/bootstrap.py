# fastapi_ddd/core/events/bootstrap.py
from importlib import import_module
from typing import Callable
from fastapi_ddd.core.config import INSTALLED_DOMAINS
from fastapi_ddd.core.events.event_bus import EventBus


def register_domain_event_handlers(bus: EventBus) -> None:
    """
    Iterate installed domains and call their register_event_handlers(bus)
    if available. Keeps main.py small and domains self-contained.
    """
    for domain in INSTALLED_DOMAINS:
        mod_path = f"fastapi_ddd.domains.{domain}.event_handlers"
        try:
            mod = import_module(mod_path)
        except ModuleNotFoundError:
            continue

        func: Callable[[EventBus], None] | None = getattr(
            mod, "register_event_handlers", None
        )
        if callable(func):
            func(bus)
