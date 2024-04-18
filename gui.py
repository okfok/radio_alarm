import asyncio
import tkinter as tk

from async_tkinter_loop import async_handler, async_mainloop

import core
import events
import models
from radio_alarm import init

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

last_update_label = tk.Label(root, text="Last Status: ")
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
async def set_last_update(event: models.StatusChangeEvent):
    last_update_label['text'] = f"Last Status: {event.status.lastUpdate}"
    status_label['text'] = f"Status: {
        ' '.join(map(lambda x: x.type, event.status.activeAlerts)) if len(event.status.activeAlerts) > 0 else 'Clear'
    }"


start_button.config(command=async_handler(start))
stop_button.config(command=async_handler(stop))

last_update_label.pack()
status_label.pack()
start_button.pack()
stop_button.pack()

if __name__ == '__main__':
    async_mainloop(root)
