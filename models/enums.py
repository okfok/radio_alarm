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
    none = "none"
    copy_file = "copy_file"
    windows_application_shortcut = "windows_application_shortcut"
    windows_powershell_application_shortcut = "windows_powershell_application_shortcut"
    local_console_execute = "local_console_execute"

    py_auto_gui_shortcut = "py_auto_gui_shortcut"
    power_shell_shortcut = "power_shell_shortcut"
