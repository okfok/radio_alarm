import asyncio
from asyncio import subprocess
from typing import Literal, List, Dict

import pyautogui
import pygetwindow
from pydantic import Field

import exceptions
from models.actions import AlertAction
from models.enums import AlertEventType, ActionType, AlertType
from models.events import AlertEvent


class WinAppShortcutAction(AlertAction):
    type: Literal[ActionType.windows_application_shortcut] = Field(
        default=ActionType.windows_application_shortcut
    )
    window_name: str = Field(default_factory=str)
    shortcut: Dict[AlertType, Dict[AlertEventType, List[str]]] = Field(default_factory=dict)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        windows = list(filter(lambda x: x.title == self.window_name, pygetwindow.getWindowsWithTitle(self.window_name)))

        if len(windows) == 0:
            raise exceptions.WinWindowNotFoundException(f"Window: {self.window_name} Not Found")
        for window in windows:
            window.minimize()
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
    shortcut: Dict[AlertType, Dict[AlertEventType, str]] = Field(default_factory=dict)

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
