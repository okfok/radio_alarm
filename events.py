import asyncio
import datetime

import pydantic

import exceptions
from logs import logger

from pydantic import TypeAdapter

import core
import aiohttp
import models
from client import Client


async def alarm_trigger(event: models.AlertEvent, silent: bool = False):
    logger.info(f'Alert action enter: {event}')

    if silent:
        logger.info(f'Alert action silent(forced)')

    if core.conf.reginId != event.alert.regionId:
        logger.info(f'Alert action silent(wrong regionId)')
        return

    for action in core.conf.actions:
        try:
            await action.act(event)
            logger.info(f'Alert action({action.type}) Finished')
        except exceptions.EventActionException as exc:
            logger.info(f'Alert action({action.type}) Failed: {exc}')

    logger.info(f'Alert action exit')


async def request_status():
    try:
        logger.debug(f'Status check {datetime.datetime.now()}')
        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=core.conf.enable_ssl_validation)
        ) as session:
            response = await Client(session, core.conf.api_key, core.conf.api_base_url).get_alerts(core.conf.reginId)
        logger.debug(f'Packet received: {response}')
        return response
    except aiohttp.ClientError as exc:
        logger.exception(exc)
        return
    except TimeoutError as exc:
        logger.exception(exc)
        return


async def periodic_check_alarm(is_start: bool = False):
    response = await request_status()
    if response is None:
        return

    status = core.Status()

    try:
        regions = TypeAdapter(list[models.Region]).validate_python(response)
    except pydantic.ValidationError as err:
        logger.exception(err)
        return

    new = []
    old = []
    _all = []

    for region in regions:
        if region.regionId == core.conf.reginId:
            if status.model.lastUpdate == region.lastUpdate:
                return

            logger.info(f'Status changed {status.model.lastUpdate} -> {region.lastUpdate}')
            status.model.lastUpdate = region.lastUpdate

            _all += region.activeAlerts

            for alert in region.activeAlerts:
                if alert not in status.model.activeAlerts:
                    new.append(alert)

            for alert in status.model.activeAlerts:
                if alert not in region.activeAlerts:
                    old.append(alert)

    if not is_start:
        for i in old:
            await alarm_trigger(models.AlertEvent(alert=i, type=models.AlertEventType.end))
            status.model.activeAlerts.remove(i)

        for i in new:
            await alarm_trigger(models.AlertEvent(alert=i, type=models.AlertEventType.start))
            status.model.activeAlerts.append(i)

    status.model.activeAlerts = _all

    status.save()


async def mainloop():
    await periodic_check_alarm(True)
    while True:
        await asyncio.sleep(core.conf.check_interval)
        await periodic_check_alarm()
