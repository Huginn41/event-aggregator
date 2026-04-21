from unittest.mock import AsyncMock, MagicMock

import pytest

from provider.paginator import EventsPaginator


def make_client(pages: list[dict]) -> MagicMock:
    client = MagicMock()
    client.events = AsyncMock(return_value=pages[0])
    if len(pages) > 1:
        client.page_from_url = AsyncMock(side_effect=pages[1:])
    return client


@pytest.mark.asyncio
async def test_paginator_single_page():
    page = {
        "next": None,
        "results": [{"id": "e1"}, {"id": "e2"}],
    }
    client = make_client([page])
    paginator = EventsPaginator(client, changed_at="2000-01-01")

    events = [e async for e in paginator.iter_events()]

    assert len(events) == 2
    assert events[0]["id"] == "e1"
    client.events.assert_called_once_with("2000-01-01")


@pytest.mark.asyncio
async def test_paginator_multiple_pages():
    page1 = {
        "next": "http://host/api/events/?cursor=abc",
        "results": [{"id": "e1"}, {"id": "e2"}],
    }
    page2 = {
        "next": None,
        "results": [{"id": "e3"}],
    }
    client = make_client([page1, page2])
    paginator = EventsPaginator(client, changed_at="2000-01-01")

    events = [e async for e in paginator.iter_events()]

    assert len(events) == 3
    assert [e["id"] for e in events] == ["e1", "e2", "e3"]
    client.page_from_url.assert_called_once_with("http://host/api/events/?cursor=abc")


@pytest.mark.asyncio
async def test_paginator_empty_results():
    page = {"next": None, "results": []}
    client = make_client([page])
    paginator = EventsPaginator(client)

    events = [e async for e in paginator.iter_events()]

    assert events == []


@pytest.mark.asyncio
async def test_paginator_three_pages():
    pages = [
        {
            "next": "http://host/?cursor=p2",
            "results": [{"id": f"e{i}"} for i in range(5)],
        },
        {
            "next": "http://host/?cursor=p3",
            "results": [{"id": f"e{i}"} for i in range(5, 10)],
        },
        {"next": None, "results": [{"id": "e10"}]},
    ]
    client = make_client(pages)
    paginator = EventsPaginator(client)

    events = [e async for e in paginator.iter_events()]

    assert len(events) == 11
