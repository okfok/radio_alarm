import asyncio
import datetime
import os
from asyncio import subprocess
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


class EventType(str, Enum):
    none = 'none'
    alert = 'alert'
    status_change = 'status_change'


class AlertEventType(str, Enum):
    start = "start"
    end = "end"


class Alert(BaseModel):
    regionId: str
    regionType: RegionType
    type: AlertType
    lastUpdate: datetime.datetime

    def __eq__(self, other: 'Alert'):
        return self.regionId == other.regionId and self.type == other.type


class Event(BaseModel):
    type: Literal[EventType.none]


class AlertEvent(Event):
    type: Literal[EventType.alert] = Field(default=EventType.alert)
    alert_type: AlertEventType
    alert: Alert


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


class ActionType(str, Enum):
    none = 'None'
    copy_file = 'Copy File'
    windows_application_shortcut = "Win Shortcut"
    windows_powershell_application_shortcut = "Win PowerShell Shortcut"
    local_console_execute = "Local Console Execute"


class Action(BaseModel):
    type: Literal[ActionType.none]

    async def act(self, event: Event):
        raise NotImplementedError()


class AlertAction(Action):
    timetable: Timetable = Field(default_factory=Timetable)

    async def act(self, event: AlertEvent) -> None:
        if not self.is_in_timetable():
            raise exceptions.OutOfTimeTableException()

    def is_in_timetable(self) -> bool:
        return self.timetable.is_in_timetable(datetime.datetime.now())


class CopyFileAction(AlertAction):
    type: Literal[ActionType.copy_file] = Field(default=ActionType.copy_file)
    source_files: dict[AlertType, dict[AlertEventType, str]] = Field(default_factory=dict)
    destination_folder: str = Field(default_factory=str)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        try:
            os.system(f'copy "{self.source_files[event.alert.type][event.alert_type]}" "{self.destination_folder}"')
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class WinAppShortcutAction(AlertAction):
    type: Literal[ActionType.windows_application_shortcut] = Field(
        default=ActionType.windows_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut: dict[AlertType, dict[AlertEventType, list[str]]] = Field(default_factory=dict)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        windows = list(filter(lambda x: x.title == self.window_name, pygetwindow.getWindowsWithTitle(self.window_name)))

        if len(windows) == 0:
            raise exceptions.WinWindowNotFoundException(f"Window: {self.window_name} Not Found")
        for window in windows:
            window.minimize()  # TODO: focus rework
            window.maximize()

            await asyncio.sleep(0.2)
            try:
                pyautogui.hotkey(*self.shortcut[event.alert.type][event.alert_type])
            except KeyError:
                raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class WinAppPSShortcutAction(AlertAction):
    type: Literal[ActionType.windows_powershell_application_shortcut] = Field(
        default=ActionType.windows_powershell_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut: dict[AlertType, dict[AlertEventType, str]] = Field(default_factory=dict)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        try:
            stdout, stderr = await (
                await subprocess.create_subprocess_exec(
                    "powershell", "-Command",
                    f"""
                        Add-Type -AssemblyName Microsoft.VisualBasic;
                        [Microsoft.VisualBasic.Interaction]::AppActivate("{self.window_name}");
                        """,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            ).communicate()

            if stderr:
                raise exceptions.WinWindowNotFoundException(f'[stderr]\n{stderr.decode()}')

            stdout, stderr = await (
                await subprocess.create_subprocess_exec(
                    "powershell", "-Command",
                    f"""
                        Add-Type -AssemblyName System.Windows.Forms
                        [System.Windows.Forms.SendKeys]::SendWait('{self.shortcut[event.alert.type][event.alert_type]}')
                        """,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            ).communicate()

            if stderr:
                raise exceptions.RadioAlarmException(f'UNKNOWN EXCEPTION: [stderr]\n{stderr.decode()}')

        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class LocalConsoleExecuteAction(AlertAction):
    type: Literal[ActionType.local_console_execute] = Field(
        default=ActionType.local_console_execute
    )
    commands: dict[AlertType, dict[AlertEventType, str]] = Field(default_factory=dict)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        try:
            os.system(self.commands[event.alert.type][event.alert_type])
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    check_interval: int = Field(default=10)
    api_base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)
    enable_ssl_validation: bool = Field(default=True)
    actions: list[CopyFileAction | WinAppShortcutAction | WinAppPSShortcutAction | LocalConsoleExecuteAction] \
        = Field(default_factory=list, discriminator='type')


class StatusModel(BaseModel):
    lastUpdate: datetime.datetime = Field(default_factory=datetime.datetime.now)
    activeAlerts: list[Alert] = Field(default_factory=list)


class StatusChangeEvent(Event):
    type: Literal[EventType.status_change] = Field(default=EventType.status_change)
    status: StatusModel

