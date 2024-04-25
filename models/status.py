import datetime
from typing import List

from pydantic import BaseModel, Field

from models.api import Alert


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: List[Alert] = Field(default_factory=list)
