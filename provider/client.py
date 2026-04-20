from typing import Any

import httpx

from core.config import settings


class EventsProviderClient:
    def __init__(
            self,
            base_url: str | None = None,
            api_key: str | None = None,
    ) -> None:
        self._base_url = base_url or settings.events_api_url
        self._api_key = api_key or settings.events_api_key

    def _headers(self):
        return {"x-api-key": self._api_key}

    async def events(self, changed_at: str, cursor: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/events/",
                params=params,
                headers=self._headers(),
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()

    async def page_from_url(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers(),
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.json()

    async def seats(self, event_id: str) -> list[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/api/events/{event_id}/seats/",
                headers=self._headers(),
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("seats", [])

    async def register(
            self,
            event_id: str,
            first_name: str,
            last_name: str,
            email: str,
            seat: str,
    ) -> str:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/api/events/{event_id}/register/",
                headers=self._headers(),
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "seat": seat,
                    "email": email,
                },
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()
            return data["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="DELETE",
                url=f"{self._base_url}/api/events/{event_id}/unregister/",
                headers=self._headers(),
                json={"ticket_id": ticket_id},
                follow_redirects=True,
            )
            response.raise_for_status()
            return True