import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    HealthResponse,
    SyncResponse,
    EventsListResponse,
    EventDetail,
    SeatsResponse,
    CreateTicketResponse,
    CreateTicketRequest,
    CancelTicketResponse,
)
from api.usecases import (
    GetSeatsUsecase,
    EventNotFound,
    EventNotPublished,
    CreateTicketUsecase,
    CancelTicketUsecase,
    TicketNotFound,
)
from database.db import get_session
from database.repositories import EventRepository, TicketRepository
from provider.client import EventsProviderClient

router = APIRouter()
logger = logging.getLogger(__name__)


def _pagination_url(request: Request, page: int, page_size: int):
    base = str(request.base_url).rstrip("/")
    path = request.url.path
    params = dict(request.query_params)
    params["page"] = str(page)
    params["page_size"] = str(page_size)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}{path}?{query}"


@router.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok"}


@router.post("/sync/trigger", response_model=SyncResponse)
async def trigger_sync():
    from sync.sync_worker import run_sync

    asyncio.create_task(run_sync())
    return {"status": "sync started"}


@router.get("/events", response_model=EventsListResponse)
async def list_events(
    request: Request,
    date_from: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_session),
):
    repo = EventRepository(db)
    parsed_date: Optional[datetime] = None
    if date_from:
        try:
            parsed_date = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD."
            )

    offset = (page - 1) * page_size
    total, events = await repo.event_list(
        date_from=parsed_date, offset=offset, limit=page_size
    )

    next_url = None
    prev_url = None

    if offset + page_size < total:
        next_url = _pagination_url(request, page + 1, page_size)
    if page > 1:
        prev_url = _pagination_url(request, page - 1, page_size)

    results = []

    for event in events:
        results.append(
            {
                "id": event.id,
                "name": event.name,
                "place": {
                    "id": event.place.id,
                    "name": event.place.name,
                    "city": event.place.city,
                    "address": event.place.address,
                },
                "event_time": event.event_time,
                "registration_deadline": event.registration_deadline,
                "status": event.status,
                "number_of_visitors": event.number_of_visitors,
            }
        )

    return {
        "count": total,
        "next": next_url,
        "previous": prev_url,
        "results": results,
    }


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event(event_id: str, db: AsyncSession = Depends(get_session)):
    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "id": event.id,
        "name": event.name,
        "place": {
            "id": event.place.id,
            "name": event.place.name,
            "city": event.place.city,
            "address": event.place.address,
            "seats_pattern": event.place.seats_pattern,
        },
        "event_time": event.event_time,
        "registration_deadline": event.registration_deadline,
        "status": event.status,
        "number_of_visitors": event.number_of_visitors,
    }


@router.get("/events/{event_id}/seats", response_model=SeatsResponse)
async def get_seats(event_id: str, db: AsyncSession = Depends(get_session)):
    client = EventsProviderClient()
    repo = EventRepository(db)
    usecase = GetSeatsUsecase(client=client, events=repo)

    try:
        seats = await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")

    return {"event_id": event_id, "available_seats": seats}


@router.post(
    "/tickets", response_model=CreateTicketResponse, status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    body: CreateTicketRequest, db: AsyncSession = Depends(get_session)
):
    client = EventsProviderClient()
    event_repo = EventRepository(db)
    ticket_repo = TicketRepository(db)

    usecase = CreateTicketUsecase(client=client, events=event_repo, tickets=ticket_repo)

    try:
        ticket_id = await usecase.do(
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except Exception as exc:
        logger.exception("Registration failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    return {"ticket_id": ticket_id}


@router.delete("/tickets/{ticket_id}", response_model=CancelTicketResponse)
async def cancel_ticket(ticket_id: str, db: AsyncSession = Depends(get_session)):
    client = EventsProviderClient()
    event_repo = EventRepository(db)
    ticket_repo = TicketRepository(db)

    usecase = CancelTicketUsecase(client=client, events=event_repo, tickets=ticket_repo)

    try:
        await usecase.do(ticket_id)
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except Exception as exc:
        logger.exception("Cancellation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True}
