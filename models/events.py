import datetime
from typing import Literal, List

from pydantic import BaseModel, Field

from models.api import Alert, Region
from models.enums import EventType, AlertEventType
from models.status import StatusModel


class Event(BaseModel):
    type: Literal[EventType.none]


class AlertEvent(Event):
    type: Literal[EventType.alert] = Field(default=EventType.alert)
    alert_type: AlertEventType
    alert: Alert


class StatusChangeEvent(Event):
    type: Literal[EventType.status_change] = Field(default=EventType.status_change)
    status: StatusModel


class StatusReceivedEvent(Event):
    type: Literal[EventType.status_receive] = Field(default=EventType.status_receive)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    regions: List[Region]
    is_start: bool = Field(default=False)
