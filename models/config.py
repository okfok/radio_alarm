import sys
from typing import List, Union

from pydantic import BaseModel, Field

from models.actions import AlertAction

if sys.platform == "win32":
    from models.win_actions import *

AlertActionTypes = Union[tuple(AlertAction.__subclasses__())]


class ConfigModel(BaseModel):
    reginId: str = Field(default='0')
    check_interval: int = Field(default=10)
    api_base_url: Union[str, None] = Field(default=None)
    api_key: Union[str, None] = Field(default=None)
    enable_ssl_validation: bool = Field(default=True)
    actions: List[AlertActionTypes] = Field(default_factory=list, discriminator='type')
