import asyncio
from asyncio import subprocess
from typing import Literal, List, Dict, Union, Optional

import pyautogui
import pygetwindow
from pydantic import Field

import exceptions
from models import Timetable
from models.actions import AlertAction
from models.enums import AlertEventType, ActionType, AlertType
from models.events import AlertEvent


class PyAutoGuiShortcut(AlertAction):
    type: Literal[ActionType.py_auto_gui_shortcut] = Field(
        default=ActionType.py_auto_gui_shortcut
    )
    shortcut: Dict[AlertType, Dict[AlertEventType, List[str]]] = Field(default_factory=dict)
    timetable: Optional[Timetable] = Field(default=None)

    async def act(self, event: AlertEvent) -> None:

        await asyncio.sleep(0.2)
        try:
            pyautogui.hotkey(*self.shortcut[event.alert.type][event.alert_type])
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class PSShortcut(AlertAction):
    type: Literal[ActionType.power_shell_shortcut] = Field(
        default=ActionType.power_shell_shortcut
    )
    shortcut: Dict[AlertType, Dict[AlertEventType, str]] = Field(default_factory=dict)
    timetable: Optional[Timetable] = Field(default=None)

    async def act(self, event: AlertEvent) -> None:
        await asyncio.sleep(0.2)

        try:
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


class WinAppShortcutAction(AlertAction):
    type: Literal[ActionType.windows_application_shortcut] = Field(
        default=ActionType.windows_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut_action: Union[PyAutoGuiShortcut, PSShortcut] = Field(default=None)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        windows = list(filter(lambda x: x.title == self.window_name, pygetwindow.getWindowsWithTitle(self.window_name)))

        if len(windows) == 0:
            raise exceptions.WinWindowNotFoundException(f"Window: {self.window_name} Not Found")
        for window in windows:
            window.minimize()
            window.maximize()

            await self.shortcut_action.act(event)


class WinAppPSShortcutAction(AlertAction):
    type: Literal[ActionType.windows_powershell_application_shortcut] = Field(
        default=ActionType.windows_powershell_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut_action: Union[PyAutoGuiShortcut, PSShortcut] = Field(default=None)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

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

        await self.shortcut_action.act(event)
