import asyncio
import logging
from datetime import datetime

import aiohttp
from ukrainealarm.client import Client

logging.basicConfig(level=logging.DEBUG)

loop = asyncio.new_event_loop()

def alarm_trigger():
    # TODO: Timetable check
    pass


async def request_status(client):
    try:
        pass
    except Exception as exc:
        pass
    logging.getLogger(__name__).info(f'Status check')
    if True:  # TODO: check if status changed
        alarm_trigger()


async def mainloop():
    async with aiohttp.ClientSession() as session:
        client = Client(session, "[YOUR_API_KEY]")
        try:
            while True:
                await request_status(client)
                await asyncio.sleep(2)
        finally:
            del client


loop.run_until_complete(mainloop())
