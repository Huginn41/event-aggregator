from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PlaceSchema(BaseModel):
    id: str
    name: str
    city: str
    address: str
    seats_pattern: Optional[str] = None

    model_config = {"from_attributes": True}


class PlaceDetailSchema(PlaceSchema):
    seats_pattern: Optional[str] = None


class EventListItem(BaseModel):
    id: str
    name: str
    place: PlaceSchema
    event_time: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}


class EventDetail(BaseModel):
    id: str
    name: str
    place: PlaceDetailSchema
    event_time: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}


class EventsListResponse(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[EventListItem]


class SeatsResponse(BaseModel):
    event_id: str
    available_seats: list[str]


class CreateTicketRequest(BaseModel):
    event_id: str
    first_name: str
    last_name: str
    email: EmailStr
    seat: str


class CreateTicketResponse(BaseModel):
    ticket_id: str


class CancelTicketResponse(BaseModel):
    success: bool


class HealthResponse(BaseModel):
    status: str


class SyncResponse(BaseModel):
    status: str
