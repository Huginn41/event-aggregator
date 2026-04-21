from datetime import datetime
from typing import Any


from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event, Place, Ticket, SyncData


class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, event_id) -> Event | None:
        result = await self._session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def event_list(
        self,
        date_from: datetime,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[int, list[Event]]:

        query = select(Event)
        count_query = select(Event)

        if date_from:
            query = query.where(Event.event_time >= date_from)
            count_query = count_query.where(Event.event_time >= date_from)

        from sqlalchemy import func

        result_count = await self._session.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = result_count.scalar_one()

        result = await self._session.execute(
            query.order_by(Event.event_time).offset(offset).limit(limit)
        )

        return total, list(result.scalars().all())

    async def sync_data(
        self,
        event_data: dict[str, Any],
        place_data: dict[str, Any],
    ) -> None:
        place_update = (
            insert(Place)
            .values(
                id=place_data["id"],
                name=place_data["name"],
                city=place_data["city"],
                address=place_data["address"],
                seats_pattern=place_data.get("seats_pattern"),
                changed_at=place_data.get("changed_at"),
                created_at=place_data.get("created_at"),
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": place_data["name"],
                    "city": place_data["city"],
                    "address": place_data["address"],
                    "seats_pattern": place_data.get("seats_pattern"),
                    "changed_at": place_data.get("changed_at"),
                },
            )
        )
        await self._session.execute(place_update)

        event_update = (
            insert(Event)
            .values(
                id=event_data["id"],
                name=event_data["name"],
                place_id=place_data["id"],
                event_time=event_data.get("event_time"),
                registration_deadline=event_data.get("registration_deadline"),
                status=event_data.get("status", "new"),
                number_of_visitors=event_data.get("number_of_visitors", 0),
                changed_at=event_data.get("changed_at"),
                created_at=event_data.get("created_at"),
                status_changed_at=event_data.get("status_changed_at"),
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": event_data["name"],
                    "place_id": place_data["id"],
                    "event_time": event_data.get("event_time"),
                    "registration_deadline": event_data.get("registration_deadline"),
                    "status": event_data.get("status", "new"),
                    "number_of_visitors": event_data.get("number_of_visitors", 0),
                    "changed_at": event_data.get("changed_at"),
                    "status_changed_at": event_data.get("status_changed_at"),
                },
            )
        )
        await self._session.execute(event_update)
        await self._session.commit()


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:

        ticket = Ticket(
            id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            created_at=datetime.now(),
        )
        self._session.add(ticket)
        await self._session.commit()
        return ticket

    async def ticket_by_id(self, ticket_id) -> Ticket | None:
        result = await self._session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def unregiser(self, ticket_id: str) -> None:
        ticket = await self.ticket_by_id(ticket_id)
        if ticket:
            await self._session.delete(ticket)
            await self._session.commit()


class SyncMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self) -> SyncData:
        result = await self._session.execute(select(SyncData).limit(1))
        sync_data = result.scalar_one_or_none()
        if not sync_data:
            sync_data = SyncData(sync_status="pending")
            self._session.add(sync_data)
            await self._session.commit()
        return sync_data

    async def update(
        self,
        last_sync_time: datetime | None = None,
        last_changed_at: str | None = None,
        sync_status: str | None = None,
    ) -> None:
        sync_data = await self.get_or_create()
        if last_sync_time is not None:
            sync_data.last_sync_time = last_sync_time
        if last_changed_at is not None:
            sync_data.last_changed_at = last_changed_at
        if sync_status is not None:
            sync_data.sync_status = sync_status
        await self._session.commit()
