

from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
)

class PlaceResponse(BaseModel):
    id: str
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: str
    name: str
    place: PlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Registration(BaseModel):
    first_name: str
    last_name: str
    seat: str
    email: EmailStr