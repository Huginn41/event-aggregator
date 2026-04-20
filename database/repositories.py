from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event


class EventRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, event_id) -> Event | None:
        result = await self._session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def event_list(
            self,
            date_from: datetime,
            offset: int = 0,
            limit: int =20,
    ) -> tuple[int, list[Event]]:

        query = select(Event)
        count_query= select(Event)

        if date_from:
            query = query.where(Event.event_time >= date_from)
            count_query = count_query.where(Event.event_time >= date_from)

        from sqlalchemy import func

        result_count = self._session.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = result_count.scalar_one()

        result = await self._session.execute(
            query.order_by(Event.event_time).offset(offset).limit(limit)
        )

        return total, list(result.scalars().all())

    

