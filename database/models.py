from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import (
    DateTime,
    String,
    Integer,
    UUID,
    ForeignKey,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.db import Base


class EventStatus(str, Enum):
    NEW = "new"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    seats_pattern: Mapped[str] = mapped_column(String, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="place",
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[EventStatus] = mapped_column(String, nullable=False)
    number_of_visitors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    place_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("places.id"),
        nullable=False,
    )
    place: Mapped["Place"] = relationship(back_populates="events")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    seat: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )
    event: Mapped["Event"] = relationship(back_populates="tickets")


class SyncData(Base):
    __tablename__ = "sync_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=uuid.uuid4
    )
    last_sync_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_changed_at: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    sync_status: Mapped[str] = mapped_column(String, nullable=False)
