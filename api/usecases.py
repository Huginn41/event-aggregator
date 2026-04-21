import logging
import typing
from datetime import datetime

from core.cache import seats_cache

logger = logging.getLogger(__name__)


class EventsProviderClientProtocol(typing.Protocol):
    async def seats(self, event_id: str) -> list[str]: ...

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str: ...

    async def unregister(self, event_id: str, ticket_id: str) -> bool: ...


class EventRepositoryProtocol(typing.Protocol):
    async def get(self, event_id: str): ...

    async def list_events(
        self,
        date_from: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[int, list]: ...


class TicketRepositoryProtocol(typing.Protocol):
    async def create(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ): ...

    async def get(self, ticket_id: str): ...

    async def delete(self, ticket_id: str) -> None: ...


class EventNotFound(Exception):
    pass


class EventNotPublished(Exception):
    pass


class TicketNotFound(Exception):
    pass


class SeatNotAvailable(Exception):
    pass


class GetSeatsUsecase:
    def __init__(
        self,
        client: EventsProviderClientProtocol,
        events: EventRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events

    async def do(self, event_id: str) -> list[str]:
        event = await self._events.get(event_id)
        if not event:
            raise EventNotFound(event_id)

        if event.status != "published":
            raise EventNotPublished(event_id)

        cached = seats_cache.get(event_id)
        if cached is not None:
            return cached

        seats = await self._client.seats(event_id)
        seats_cache.set(event_id, seats)
        return seats


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProtocol,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        event = await self._events.get(event_id)
        if not event:
            raise EventNotFound(event_id)

        if event.status != "published":
            raise EventNotPublished(event_id)

        ticket_id = await self._client.register(
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        await self._tickets.create(
            ticket_id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )
        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProtocol,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(self, ticket_id: str) -> bool:
        ticket = await self._tickets.get(ticket_id)
        if not ticket:
            raise TicketNotFound(ticket_id)

        event = await self._events.get(ticket.event_id)
        if not event:
            raise EventNotFound(ticket.event_id)

        await self._client.unregister(event_id=ticket.event_id, ticket_id=ticket_id)
        await self._tickets.delete(ticket_id)
        return True
