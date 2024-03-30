import asyncio
import datetime
import logging
import os

from pydantic import TypeAdapter

import core
import aiohttp
# from ukrainealarm.client import Client
from uasiren.client import Client
import models

logger = logging.getLogger(__name__)


def alarm_trigger(alarm: models.Alert, event: models.AlertEvent):
    logger.info(f'Alarm trigger enter: {event}: {alarm}')

    if not core.conf.timetable.is_in_timetable(datetime.datetime.now()):
        logger.info(f'Alarm trigger: {event}: {alarm} silent(out of timetable)')
        return

    if datetime.datetime.now(datetime.UTC) - alarm.lastUpdate > core.conf.skip_interval:
        logger.info(f'Alarm trigger: {event}: {alarm} silent(skip interval)')
        return

    if core.conf.reginId != alarm.regionId:
        logger.info(f'Alarm trigger: {event}: {alarm} silent(wrong regionId)')
        return

    try:
        os.system(f'copy {core.conf.source_files[alarm.type][event]} {core.conf.destination_folder}')
        logger.info(f'Alarm trigger: {event}: {alarm} finished')
    except KeyError as err:
        logger.warning("Alert type not configured!")
        logger.error(err)


async def request_status(client):
    try:
        logger.info(f'Status check')
        response = await client.get_alerts(core.conf.reginId)
        logger.info(f'Packet received: {response}')
#         response = """[
#   {
#     "regionId": "0",
#     "regionType": "State",
#     "regionName": "Test region",
#     "regionEngName": "Test region",
#     "lastUpdate": "2024-03-28T22:12:50.204Z",
#     "activeAlerts": [
#       {
#         "regionId": "0",
#         "regionType": "State",
#         "type": "UNKNOWN",
#         "lastUpdate": "2024-03-28T22:10:50.204Z"
#       }
#     ]
#   }
# ]"""
        # TODO: handling exceptions
        status = core.Status()
        regions = TypeAdapter(list[models.Region]).validate_python(response)

        new = []
        old = []

        for region in regions:
            if region.regionId == core.conf.reginId:
                if status.model.lastUpdate == region.lastUpdate:
                    return

                logger.info(f'Status changed {status.model.lastUpdate} -> {region.lastUpdate}')
                status.model.lastUpdate = region.lastUpdate
                status.save()

                for alert in region.activeAlerts:
                    if alert not in status.model.activeAlerts:
                        new.append(alert)

                for alert in status.model.activeAlerts:
                    if alert not in region.activeAlerts:
                        old.append(alert)

        for i in new:
            alarm_trigger(i, models.AlertEvent.start)
            status.model.activeAlerts.append(i)

        for i in old:
            alarm_trigger(i, models.AlertEvent.end)
            status.model.activeAlerts.remove(i)

        # status.model.activeAlerts = new
        status.save()

    except Exception as exc:
        raise exc


async def mainloop():
    async with aiohttp.ClientSession() as session:
        # client = Client(session, core.conf.api_key)
        client = Client(session)
        try:
            while True:
                await request_status(client)
                await asyncio.sleep(core.conf.check_interval)
        finally:
            del client
