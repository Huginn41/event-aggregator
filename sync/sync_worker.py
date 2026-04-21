import logging
from datetime import datetime

from database.db import async_session

from database.repositories import SyncMetadataRepository, EventRepository

from provider.client import EventsProviderClient
from provider.paginator import INITIAL_CHANGED_AT, EventsPaginator

logger = logging.getLogger(__name__)


async def run_sync() -> None:
    logger.info("Starting events sync...")
    async with async_session() as session:
        sync_repo = SyncMetadataRepository(session)
        event_repo = EventRepository(session)

        sync_data = await sync_repo.get_or_create()
        changed_at = sync_data.last_changed_at or INITIAL_CHANGED_AT

        await sync_repo.update(sync_status="running")

        client = EventsProviderClient()
        paginator = EventsPaginator(client=client, changed_at=changed_at)

        synced = 0
        latest_changed_at = changed_at

        try:
            async for event in paginator.iter_events():
                place_data = event.get("place", {})
                await event_repo.sync_data(event, place_data)
                synced += 1

                event_changed = event.get("changed_at", "")
                if event_changed:

                    try:
                        dt_new = datetime.fromisoformat(event_changed).replace(tzinfo=None)
                        dt_current = datetime.fromisoformat(latest_changed_at).replace(tzinfo=None)
                        if dt_new > dt_current:
                            latest_changed_at = dt_new.isoformat()
                    except (ValueError, TypeError):
                        pass
            await sync_repo.update(
                last_sync_time=datetime.now(),
                last_changed_at=latest_changed_at,
                sync_status="success",
            )
            logger.info("Sync completed. Synced %d events.", synced)

        except Exception as exc:
            await sync_repo.update(sync_status="error")
            logger.exception("Sync failed: %s", exc)
            raise
