import asyncio
import datetime

import exceptions
from logs import logger

from pydantic import TypeAdapter

import core
import aiohttp
import models
from client import Client


async def alarm_trigger(alert: models.Alert, event: models.AlertEvent, silent: bool = False):
    logger.info(f'Alert trigger enter: {event}: {alert}')

    if silent:
        logger.info(f'Alert trigger: {event}: {alert} silent(forced)')

    if core.conf.reginId != alert.regionId:
        logger.info(f'Alert trigger: {event}: {alert} silent(wrong regionId)')
        return

    for trigger in core.conf.triggers:
        try:
            await trigger.action(alert, event)
            logger.info(f'Alert trigger({trigger.trigger_type}): {event}: {alert} Finished')
        except exceptions.TriggerException as exc:
            logger.info(f'Alert trigger({trigger.trigger_type}): {event}: {alert} Failed: {exc}')

    logger.info(f'Alert trigger exit: {event}: {alert}')


async def request_status(client):
    try:
        logger.debug(f'Status check {datetime.datetime.now()}')
        response = await client.get_alerts(core.conf.reginId)
        logger.debug(f'Packet received: {response}')
        return response
    except aiohttp.client_exceptions.ClientResponseError as exc:
        logger.exception(exc)
        return
    except aiohttp.client_exceptions.ClientConnectorError as exc:
        logger.exception(exc)
        return
    except TimeoutError as exc:
        logger.exception(exc)
        return


async def periodic_check_alarm(client, is_start: bool = False):
    response = await request_status(client)
    if response is None:
        return

    status = core.Status()
    regions = TypeAdapter(list[models.Region]).validate_python(response)

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
            await alarm_trigger(i, models.AlertEvent.end)
            status.model.activeAlerts.remove(i)

        for i in new:
            await alarm_trigger(i, models.AlertEvent.start)
            status.model.activeAlerts.append(i)

    status.model.activeAlerts = _all

    status.save()


async def mainloop():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=core.conf.enable_ssl_validation)) as session:
        client = Client(session, core.conf.api_key)
        try:
            await periodic_check_alarm(client, True)
            while True:
                await asyncio.sleep(core.conf.check_interval)  # TODO: after alert sleep interval
                await periodic_check_alarm(client)
        finally:
            del client
