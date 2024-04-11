import asyncio
from types import coroutine

import pydantic

import exceptions
import models
from logs import logger

loop = asyncio.new_event_loop()


class Config:
    _actions: list[models.Action] = []
    _conf: models.ConfigModel = None

    def __new__(cls) -> models.ConfigModel:
        return cls._conf

    @classmethod
    def load(cls):
        try:
            with open('conf.json', 'r', encoding='utf-8') as f:
                cls._conf = models.ConfigModel.parse_raw(f.read())
                cls.register_config_actions()

        except FileNotFoundError as err:
            logger.error("Config file not found! Generating template.")
            cls._conf = models.ConfigModel()
            with open('conf.json', 'w', encoding='utf-8') as f:
                f.write(cls._conf.model_dump_json())
            logger.debug("Config file generated. Exiting.")
            raise err
        except pydantic.ValidationError as exc:
            raise exc
        logger.debug("Loaded successfully")

    @classmethod
    def save(cls):
        with open('conf.json', 'w', encoding='utf-8') as f:
            f.write(cls._conf.model_dump_json())

    @classmethod
    def register_action(cls, action: models.Action):
        cls._actions.append(action)

    @classmethod
    def register_config_actions(cls):
        for action in cls._conf.actions:
            cls.register_action(action)

    @classmethod
    async def call(cls, event: models.Event):
        await asyncio.gather(
            *
            (
                try_job(
                    action.act(event),
                    exceptions.EventActionException,
                    log_func=logger.info,
                    success_log=f'Alert action({action.type}) Finished',
                    fail_log=f'Alert action({action.type}) Failed:'
                )
                for action in cls._actions
            )
        )


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
