import logging
from typing import Any, AsyncIterator

from provider.client import EventsProviderClient

logger = logging.getLogger(__name__)

INITIAL_CHANGED_AT = "2000-01-01"


class EventsPaginator:

    def __init__(self, client: EventsProviderClient, changed_at: str = INITIAL_CHANGED_AT) -> None:
        self._client = client
        self._changed_at = changed_at

    async def iter_events(self) -> AsyncIterator[dict[str, Any]]:
        data = await self._client.events(self._changed_at)

        while True:
            results = data.get("results", [])
            for event in results:
                yield event

            next_url = data.get("next")
            if not next_url or not isinstance(next_url, str):
                break

            data = await self._client.page_from_url(next_url)