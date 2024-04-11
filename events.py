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

    if core.Config().reginId != event.alert.regionId:
        logger.info(f'Alert action silent(wrong regionId)')
        return

    await core.Config.call(event)

    logger.info(f'Alert action exit')


async def request_status():
    try:
        logger.debug(f'Status check {datetime.datetime.now()}')
        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=core.Config().enable_ssl_validation)
        ) as session:
            response = await Client(session, core.Config().api_key, core.Config().api_base_url).get_alerts(
                core.Config().reginId)
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
        if region.regionId == core.Config().reginId:
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
        await asyncio.sleep(core.Config().check_interval)
        await periodic_check_alarm()
