from enum import Enum


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
    status_receive = 'status_receive'


class AlertEventType(str, Enum):
    start = "start"
    end = "end"


class ActionType(str, Enum):
    none = 'None'
    copy_file = 'Copy File'
    windows_application_shortcut = "Win Shortcut"
    windows_powershell_application_shortcut = "Win PowerShell Shortcut"
    local_console_execute = "Local Console Execute"
