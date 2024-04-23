import asyncio

import aiohttp

import core
from client import Client


async def region_list():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=core.Config().enable_ssl_validation)) as session:
        print(await Client(session, core.Config().api_key).get_regions())


COMMANDS = {
    "regions": region_list
}


def console_command(command, *argv):
    try:
        core.Config.load()
        asyncio.run(COMMANDS[command](*argv))
    except KeyError:
        print("Wrong Command!")
