from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from provider.client import EventsProviderClient


@pytest.fixture
def client():
    return EventsProviderClient(base_url="http://test-host", api_key="test-key")


@pytest.mark.asyncio
async def test_events_first_page(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "next": None,
        "previous": None,
        "results": [{"id": "event-1", "name": "Test Event"}],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(
            return_value=mock_http.return_value
        )
        mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value.get = AsyncMock(return_value=mock_response)

        result = await client.events("2000-01-01")

    assert result["results"][0]["id"] == "event-1"
    mock_http.return_value.get.assert_called_once()


@pytest.mark.asyncio
async def test_events_with_cursor(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"next": None, "results": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(
            return_value=mock_http.return_value
        )
        mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value.get = AsyncMock(return_value=mock_response)

        await client.events("2000-01-01", cursor="abc123")

    call_kwargs = mock_http.return_value.get.call_args
    assert "cursor" in call_kwargs.kwargs["params"]


@pytest.mark.asyncio
async def test_register_returns_ticket_id(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"ticket_id": "ticket-uuid-123"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(
            return_value=mock_http.return_value
        )
        mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value.post = AsyncMock(return_value=mock_response)

        ticket_id = await client.register(
            event_id="event-1",
            first_name="Ivan",
            last_name="Ivanov",
            email="ivan@example.com",
            seat="A15",
        )

    assert ticket_id == "ticket-uuid-123"


@pytest.mark.asyncio
async def test_seats_returns_list(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"seats": ["A1", "A2", "B1"]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(
            return_value=mock_http.return_value
        )
        mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value.get = AsyncMock(return_value=mock_response)

        seats = await client.seats("event-1")

    assert seats == ["A1", "A2", "B1"]


@pytest.mark.asyncio
async def test_unregister_returns_true(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__ = AsyncMock(
            return_value=mock_http.return_value
        )
        mock_http.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_http.return_value.request = AsyncMock(
            return_value=mock_response
        )  # было delete

        result = await client.unregister("event-1", "ticket-1")

    assert result is True
