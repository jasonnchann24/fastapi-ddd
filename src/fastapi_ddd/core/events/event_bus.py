from collections import defaultdict
from typing import Type, Callable, Awaitable, Any, Dict, List
from sqlmodel.ext.asyncio.session import AsyncSession
from .base import DomainEvent
import asyncio


EventHandler = Callable[[DomainEvent], Awaitable[None]]
EventHandlerWithSession = Callable[[DomainEvent, AsyncSession | None], Awaitable[None]]


class EventBus:
    """
    EventBus interface
    """

    def subscribe(
        self, event_type: Type[DomainEvent], handler: EventHandlerWithSession
    ) -> None:
        raise NotImplementedError

    async def publish(
        self,
        event: DomainEvent,
        *,
        session: AsyncSession | None = None,
        raise_on_error: bool = True,
    ) -> None:
        raise NotImplementedError


class SimpleEventBus(EventBus):
    """
    In-memory implementation of EventBus
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandlerWithSession]] = (
            defaultdict(list)
        )

    def subscribe(
        self, event_type: Type[DomainEvent], handler: EventHandlerWithSession
    ) -> None:
        self._handlers[event_type].append(handler)

    async def publish(
        self,
        event: DomainEvent,
        *,
        session: AsyncSession | None = None,
        raise_on_error: bool = True,
    ) -> None:
        handlers = list(self._handlers.get(type(event), []))
        errors: list[Exception] = []

        for h in handlers:
            try:
                await h(event, session)
            except Exception as e:
                errors.append(e)
                if raise_on_error:
                    break
        if errors and raise_on_error:
            raise errors[0]
