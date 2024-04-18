import asyncio
import tkinter as tk

from async_tkinter_loop import async_handler, async_mainloop
from tzlocal import get_localzone

import core
import events
import models
from radio_alarm import init

TIME_FORMAT = '%H:%M:%S %d.%m'

init()

root = tk.Tk()

label = tk.Label(root)
label.pack()

loop = asyncio.get_event_loop()


async def mainloop():
    try:
        await events.mainloop()
    except asyncio.CancelledError:
        ...


mainloop_task = None

last_update = tk.Label(root, text="Last Update: ")
last_status = tk.Label(root, text="Last Status: ")
status_label = tk.Label(root, text="Status: ")
start_button = tk.Button(root, text="Start")
stop_button = tk.Button(root, text="Stop", state='disabled')


async def start():
    start_button['state'] = 'disabled'
    stop_button['state'] = 'normal'
    global mainloop_task
    mainloop_task = loop.create_task(events.mainloop())

    try:
        await asyncio.gather(mainloop_task)
    except asyncio.CancelledError:
        ...
    finally:
        stop_button['state'] = 'disabled'
        start_button['state'] = 'normal'


async def stop():
    global mainloop_task
    mainloop_task.cancel()


@core.EventHandler.register_callback_dec(models.EventType.status_change)
async def set_last_status(event: models.StatusChangeEvent):
    tz = get_localzone()
    local_timestamp = event.status.lastUpdate.astimezone(tz)
    last_status['text'] = f"Last Status: {local_timestamp.strftime(TIME_FORMAT)}"
    status_label['text'] = f"Status: {
    ' '.join(map(lambda x: x.type, event.status.activeAlerts))
    if len(event.status.activeAlerts) > 0
    else 'Clear'
    }"


@core.EventHandler.register_callback_dec(models.EventType.status_receive)
async def set_last_update(event: models.StatusReceivedEvent):
    last_update['text'] = f"Last Update: {event.timestamp.strftime(TIME_FORMAT)}"


start_button.config(command=async_handler(start))
stop_button.config(command=async_handler(stop))

start_button.pack()
stop_button.pack()
last_update.pack()
last_status.pack()
status_label.pack()

if __name__ == '__main__':
    async_mainloop(root)
