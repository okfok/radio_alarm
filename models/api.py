import datetime
from typing import List

from pydantic import BaseModel

from models.enums import RegionType, AlertType


class Alert(BaseModel):
    regionId: str
    regionType: RegionType
    type: AlertType
    lastUpdate: datetime.datetime

    def __eq__(self, other: 'Alert'):
        return self.regionId == other.regionId and self.type == other.type


class Region(BaseModel):
    regionId: str
    regionType: RegionType
    regionName: str
    regionEngName: str
    lastUpdate: datetime.datetime
    activeAlerts: List[Alert]
