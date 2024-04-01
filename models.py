import asyncio
import datetime
import os
import time
from enum import Enum
import pyautogui
from pygetwindow import Win32Window

from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


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


class TriggerType(int, Enum):
    copy_file = 0
    application_shortcut = 1


class Trigger(BaseModel):
    trigger_type: TriggerType

    def action(self, alert: Alert, event: AlertEvent) -> bool:
        raise NotImplementedError()


class CopyTrigger(Trigger):
    trigger_type: TriggerType = TriggerType.copy_file
    source_files: dict[AlertType, dict[AlertEvent, str]]
    destination_folder: str

    def action(self, alert: Alert, event: AlertEvent) -> bool:
        try:
            os.system(f'copy "{self.source_files[alert.type][event]}" "{self.destination_folder}"')
            return True
        except KeyError as err:
            logger.error("Alert type not configured!")
            logger.error(err)
            return False


class ShortcutTrigger(Trigger):
    trigger_type: TriggerType = TriggerType.application_shortcut
    window_name: str
    shortcut: dict[AlertType, dict[AlertEvent, list[str]]]

    def action(self, alert: Alert, event: AlertEvent) -> bool:
        # TODO: exception handling
        win: Win32Window = pyautogui.getWindowsWithTitle(self.window_name)[0]
        # win.activate()
        if not win.isActive:  # TODO: focus rework
            win.minimize()
            win.maximize()
            print('remaxed')

        time.sleep(0.2)

        pyautogui.hotkey(*self.shortcut[alert.type][event])

        return True


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    check_interval: int = Field(default=10)
    timetable: Timetable = Field(default_factory=Timetable)
    api_key: str = Field(default='[API KEY]')
    triggers: list[CopyTrigger | ShortcutTrigger] = Field(default_factory=list)


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: list[Alert] = Field(default_factory=list)
