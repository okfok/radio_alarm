import datetime
import os
from typing import Literal, Dict

from pydantic import BaseModel, Field

import exceptions
from models.enums import AlertEventType, ActionType, AlertType
from models.events import AlertEvent, Event
from models.timetable import Timetable


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
    source_files: Dict[AlertType, Dict[AlertEventType, str]] = Field(default_factory=dict)
    destination_folder: str = Field(default_factory=str)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        try:
            os.system(f'copy "{self.source_files[event.alert.type][event.alert_type]}" "{self.destination_folder}"')
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")


class LocalConsoleExecuteAction(AlertAction):
    type: Literal[ActionType.local_console_execute] = Field(
        default=ActionType.local_console_execute
    )
    commands: Dict[AlertType, Dict[AlertEventType, str]] = Field(default_factory=dict)

    async def act(self, event: AlertEvent) -> None:
        await super().act(event)

        try:
            os.system(self.commands[event.alert.type][event.alert_type])
        except KeyError:
            raise exceptions.AlertTypeNotConfiguredException(f"Alert type({event.alert.type}) not configured!")
