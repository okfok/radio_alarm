import asyncio
import datetime
import os
from enum import Enum
from typing import Literal

import pyautogui
import pygetwindow
from pydantic import BaseModel, Field
import exceptions


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

    def __eq__(self, other: 'Alert'):
        return self.regionId == other.regionId and self.type == other.type


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


class TriggerType(str, Enum):
    none = 'None'
    copy_file = 'Copy'
    windows_application_shortcut = "Win Shortcut"


class Trigger(BaseModel):
    trigger_type: Literal[TriggerType.none]
    timetable: Timetable = Field(default_factory=Timetable)

    async def action(self, alert: Alert, event: AlertEvent) -> None:
        if not self.is_in_timetable():
            raise exceptions.OutOfTimeTableException()

    def is_in_timetable(self) -> bool:
        return self.timetable.is_in_timetable(datetime.datetime.now())


class CopyFileTrigger(Trigger):
    trigger_type: Literal[TriggerType.copy_file] = Field(default=TriggerType.copy_file)
    source_files: dict[AlertType, dict[AlertEvent, str]] = Field(default_factory=dict)
    destination_folder: str = Field(default_factory=str)

    async def action(self, alert: Alert, event: AlertEvent) -> None:
        await super().action(alert, event)

        try:
            os.system(f'copy "{self.source_files[alert.type][event]}" "{self.destination_folder}"')
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({alert.type}) not configured!")


class WinAppShortcutTrigger(Trigger):
    trigger_type: Literal[TriggerType.windows_application_shortcut] = Field(
        default=TriggerType.windows_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut: dict[AlertType, dict[AlertEvent, list[str]]] = Field(default_factory=dict)

    async def action(self, alert: Alert, event: AlertEvent) -> None:
        await super().action(alert, event)

        windows = list(filter(lambda x: x == self.window_name, pygetwindow.getWindowsWithTitle(self.window_name)))

        if len(windows) == 0:
            raise exceptions.WinWindowNotFoundException(f"Window: {self.window_name} Not Found")
        for window in windows:
            if window.title == self.window_name:
                window.minimize()  # TODO: focus rework
                window.maximize()

                await asyncio.sleep(0.2)
                try:
                    pyautogui.hotkey(*self.shortcut[alert.type][event])
                except KeyError:
                    raise exceptions.AlertTypeNotConfiguredException(f"Alert type({alert.type}) not configured!")


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    check_interval: int = Field(default=10)
    api_base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)
    enable_ssl_validation: bool = Field(default=True)
    triggers: list[CopyFileTrigger | WinAppShortcutTrigger] = Field(default_factory=list, discriminator='trigger_type')
    after_alert_sleep_interval: datetime.timedelta = Field(default_factory=datetime.timedelta)


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: list[Alert] = Field(default_factory=list)
