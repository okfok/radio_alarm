import asyncio
import sys
from types import coroutine
from typing import Dict, List

import pydantic

import core
import exceptions
import logs
import models
import utils
from logs import logger

loop = asyncio.new_event_loop()


class EventHandler:
    _callbacks: Dict[models.EventType, List[callable]] = {
        event_type: list() for event_type in models.EventType
    }

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def register_callback(cls, callback, event_type: models.EventType):
        cls._callbacks[event_type].append(callback)

    @classmethod
    def clear_callbacks(cls, event_type: models.EventType = None):
        if event_type is None:
            cls._callbacks = {
                event_type: list() for event_type in models.EventType
            }
        else:
            cls._callbacks[event_type] = list()

    @classmethod
    def register_callback_dec(cls, event_type: models.EventType):
        def wrapper(callback):
            cls.register_callback(callback, event_type)

        return wrapper

    @classmethod
    async def call(cls, event: models.Event):
        await asyncio.gather(
            *(
                callback(event)
                for callback in cls._callbacks[event.type]
            )
        )


class Config:
    _conf: models.ConfigModel = None

    def __new__(cls) -> models.ConfigModel:
        return cls._conf

    @classmethod
    def load(cls, file_name: str = None):
        file_name = file_name or 'conf.json'
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                cls._conf = models.ConfigModel.parse_raw(f.read())
                cls.register_config_actions()

        except FileNotFoundError as err:
            logger.error("Config file not found! Generating template.")
            cls._conf = models.ConfigModel()
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(cls._conf.model_dump_json())
            logger.debug("Config file generated. Exiting.")
            raise err
        except pydantic.ValidationError as exc:
            raise exc
        logger.debug("Loaded successfully")

    @classmethod
    def save(cls, file_name: str = None):
        file_name = file_name or 'conf.json'
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(cls._conf.model_dump_json())

    @classmethod
    def register_action(cls, action: models.Action):
        async def callback(event):
            await try_job(
                action.act(event),
                exceptions.EventActionException,
                log_func=logger.info,
                success_log=f'Alert action({action.type}) Finished',
                fail_log=f'Alert action({action.type}) Failed:'
            )

        EventHandler.register_callback(callback, models.EventType.alert)

    @classmethod
    def register_config_actions(cls):
        EventHandler.clear_callbacks(models.EventType.alert)

        for action in cls._conf.actions:
            cls.register_action(action)


class Status:
    def __init__(self):
        logger.debug("Loading status file")
        try:
            with open('status.json', 'r', encoding='utf-8') as f:
                self.model = models.StatusModel.parse_raw(f.read())
        except (FileNotFoundError, pydantic.ValidationError) as exc:
            logger.exception(exc)
            logger.warning("Status file generated.")
            self.model = models.StatusModel()

    def save(self):
        logger.debug("Saving status file")
        with open('status.json', 'w', encoding='utf-8') as f:
            f.write(self.model.model_dump_json())


async def try_job(
        job: coroutine, excs: type,

        success_callback: callable = None,
        success_callback_args: dict = None,
        success_callback_kwargs: dict = None,
        success_callback_pass_result: bool = True,

        fail_callback: callable = None,
        fail_callback_args: dict = None,
        fail_callback_kwargs: dict = None,
        fail_callback_pass_exc: bool = True,

        log_func: callable = None, success_log: str = None, fail_log: str = None,
        fail_log_append_exc: bool = True,

) -> bool:
    try:
        res = await job
        if callable(success_callback):
            kwargs = success_callback_kwargs or dict()
            args = success_callback_args or list()

            if success_callback_pass_result:
                kwargs['result'] = res

            success_callback(*args, **kwargs)

        if callable(log_func):
            log_func(success_log)

        return True
    except excs as exc:
        if callable(fail_callback):
            kwargs = fail_callback_kwargs or dict()
            args = fail_callback_args or list()

            if fail_callback_pass_exc:
                kwargs['exception'] = exc

            fail_callback(*args, **kwargs)

        if callable(log_func):
            log_func(f'{fail_log} {exc}') if fail_log_append_exc else log_func(fail_log)

        return False


def init():
    if '-c' in sys.argv:
        utils.console_command(*sys.argv[sys.argv.index('-c') + 1:])
        return
    logs.init_logger(('--debug' in sys.argv or '-d' in sys.argv))
    logs.logger.info("Starting")
    core.Config.load()

    if '--reload-conf' in sys.argv:
        core.Config.save()
