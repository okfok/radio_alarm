import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RegionType(str, Enum):
    State = "State"
    District = "District"
    Community = "Community"
    Null = "Null"


class AlertType(str, Enum):
    UNKNOWN = "UNKNOWN"
    AIR = "AIR"
    ARTILLERY = "ARTILLERY"
    URBAN_FIGHTS = "URBAN_FIGHTS"
    CHEMICAL = "CHEMICAL"
    NUCLEAR = "NUCLEAR"
    INFO = "INFO"


class AlertEvent(str, Enum):
    start = "start"
    end = "end"


class Alert(BaseModel):
    regionId: str
    regionType: RegionType
    type: AlertType
    lastUpdate: datetime.datetime


class Region(BaseModel):
    regionId: str
    regionType: RegionType
    regionName: str
    regionEngName: str
    lastUpdate: datetime.datetime
    activeAlerts: list[Alert]


class Interval(BaseModel):
    start: datetime.time
    end: datetime.time

    def is_in_interval(self, time: datetime.time):
        return self.start <= time <= self.end


class Timetable(BaseModel):
    mon: list[Interval] = Field(default_factory=list)
    tue: list[Interval] = Field(default_factory=list)
    wed: list[Interval] = Field(default_factory=list)
    thu: list[Interval] = Field(default_factory=list)
    fri: list[Interval] = Field(default_factory=list)
    sat: list[Interval] = Field(default_factory=list)
    sun: list[Interval] = Field(default_factory=list)

    def is_in_timetable(self, dt: datetime.datetime):
        intervals = {
            0: self.mon,
            1: self.tue,
            2: self.wed,
            3: self.thu,
            4: self.fri,
            5: self.sat,
            6: self.sun
        }[dt.weekday()]
        return any((interval.is_in_interval(dt.time()) for interval in intervals))


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    source_files: dict[AlertType, dict[AlertEvent, str]] = Field(default_factory=dict)
    destination_folder: str = Field(default='')
    check_interval: int = Field(default=10)
    timetable: Timetable = Field(default_factory=Timetable)
    api_key: str = Field(default='[API KEY]')
    skip_interval: datetime.timedelta = Field(default=datetime.timedelta(0, 600))


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: list[Alert] = Field(default_factory=list)
