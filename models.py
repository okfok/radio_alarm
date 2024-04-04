import asyncio
import datetime
import os
from enum import Enum
import pyautogui
import pygetwindow
from pydantic import BaseModel, Field
from logs import logger


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
    copy_file = 'Copy'
    windows_application_shortcut = "Win Shortcut"


class Trigger(BaseModel):
    trigger_type: TriggerType

    async def action(self, alert: Alert, event: AlertEvent) -> bool:
        raise NotImplementedError()


class CopyFileTrigger(Trigger):
    trigger_type: TriggerType = TriggerType.copy_file
    source_files: dict[AlertType, dict[AlertEvent, str]]
    destination_folder: str

    async def action(self, alert: Alert, event: AlertEvent) -> bool:
        try:
            os.system(f'copy "{self.source_files[alert.type][event]}" "{self.destination_folder}"')
            return True
        except KeyError as err:
            logger.error(f"Alert type({alert.type}) not configured!")
            logger.error(err)
            return False


class WinAppShortcutTrigger(Trigger):
    trigger_type: TriggerType = TriggerType.windows_application_shortcut
    window_name: str
    shortcut: dict[AlertType, dict[AlertEvent, list[str]]]

    async def action(self, alert: Alert, event: AlertEvent) -> bool:

        # TODO: exception handling
        windows = pygetwindow.getWindowsWithTitle(self.window_name)

        if len(windows) == 0:
            return False
        for win in windows:
            if win.title == self.window_name:
                win.minimize()  # TODO: focus rework
                win.maximize()

                await asyncio.sleep(0.2)
                try:
                    pyautogui.hotkey(*self.shortcut[alert.type][event])
                except KeyError as err:
                    logger.error(f"Alert type({alert.type}) not configured!")
                    logger.error(err)
                    return False

        return True


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    check_interval: int = Field(default=10)
    api_base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)
    enable_ssl_validation: bool = Field(default=True)
    timetable: Timetable = Field(default_factory=Timetable)
    triggers: list[CopyFileTrigger | WinAppShortcutTrigger] = Field(default_factory=list)
    after_alert_sleep_interval: datetime.timedelta = Field(default_factory=datetime.timedelta)


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: list[Alert] = Field(default_factory=list)
