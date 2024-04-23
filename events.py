import asyncio
import datetime

import aiohttp
import pydantic
from pydantic import TypeAdapter
from typing import List

import core
import models
from client import Client
from logs import logger


async def alarm_trigger(event: models.AlertEvent, silent: bool = False):
    logger.info(f'Alert action enter: {event}')

    if silent:
        logger.info(f'Alert action silent(forced)')

    if core.Config().reginId != event.alert.regionId:
        logger.info(f'Alert action silent(wrong regionId)')
        return

    await core.EventHandler.call(event)

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

        regions = TypeAdapter(List[models.Region]).validate_python(response)

        await core.EventHandler.call(models.StatusReceivedEvent(regions=regions))

        return regions
    except (aiohttp.ClientError, TimeoutError, pydantic.ValidationError) as exc:
        logger.exception(exc)
        return


async def periodic_check_alarm(is_start: bool = False):
    regions = await request_status()
    if regions is None:
        return

    status = core.Status()

    new = []
    old = []
    _all = []

    for region in regions:
        if region.regionId == core.Config().reginId:
            if status.model.lastUpdate == region.lastUpdate:
                if is_start:
                    await core.EventHandler.call(models.StatusChangeEvent(status=status.model, is_start=True))
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
            await alarm_trigger(models.AlertEvent(alert=i, alert_type=models.AlertEventType.end))
            status.model.activeAlerts.remove(i)

        for i in new:
            await alarm_trigger(models.AlertEvent(alert=i, alert_type=models.AlertEventType.start))
            status.model.activeAlerts.append(i)

    status.model.activeAlerts = _all

    status.save()
    await core.EventHandler.call(models.StatusChangeEvent(status=status.model))


async def mainloop():
    await periodic_check_alarm(True)
    while True:
        await asyncio.sleep(core.Config().check_interval)
        await periodic_check_alarm()
