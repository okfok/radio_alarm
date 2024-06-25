import asyncio
import os
import sys
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk
from async_tkinter_loop import async_handler, async_mainloop
from tzlocal import get_localzone

import core
import funcs
import logs
import models


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


TIME_FORMAT = '%H:%M:%S %d.%m'

core.init()

root = tk.Tk()
root.title('Radio Alarm')
root.geometry('250x250')
root.resizable(False, False)

ico = Image.open(resource_path("favicon.ico"))

root.wm_iconphoto(True, ImageTk.PhotoImage(ico))

loop = asyncio.get_event_loop()

mainloop_task = None

last_update = tk.Label(root, text="Last Update: ")
last_status = tk.Label(root, text="Last Status: ")
status_label = tk.Label(root, text="Status: off", fg='#00f')
start_button = tk.Button(root, text="Start")
stop_button = tk.Button(root, text="Stop", state='disabled')

actions_list = ttk.Labelframe(root, text="Actions")


def update_action():
    for i in list(actions_list.children.values()):
        i.destroy()

    actions = core.Config().actions
    for action in actions:
        fg = '#000'
        if action.timetable is not None and action.is_in_timetable():
            fg = '#00f'

        lb = tk.Label(actions_list, text=action.type, fg=fg)
        lb.pack()


async def start():
    start_button['state'] = 'disabled'
    stop_button['state'] = 'normal'

    global mainloop_task
    mainloop_task = loop.create_task(funcs.mainloop())

    core.Config.load()

    update_action()

    logs.logger.info("Mainloop enter")

    while True:
        try:
            await asyncio.gather(mainloop_task)
        except asyncio.CancelledError:
            logs.logger.info("Mainloop exit")
            stop_button['state'] = 'disabled'
            start_button['state'] = 'normal'
            status_label['text'] = 'Status: off'
            status_label['fg'] = '#00f'
            break
        except Exception as exc:
            logs.logger.info(exc)


async def stop():
    global mainloop_task
    mainloop_task.cancel()


@core.EventHandler.register_callback_dec(models.EventType.status_change)
async def set_last_status(event: models.StatusChangeEvent):
    tz = get_localzone()
    local_timestamp = event.status.lastUpdate.astimezone(tz)
    last_status['text'] = f"Last Status: {local_timestamp.strftime(TIME_FORMAT)}"
    status_label[
        'text'] = f"Status: {' '.join(map(lambda x: x.type, event.status.activeAlerts)) if len(event.status.activeAlerts) > 0 else 'Clear'}"
    status_label['fg'] = '#f00' if len(event.status.activeAlerts) else '#0f0'


@core.EventHandler.register_callback_dec(models.EventType.status_receive)
async def set_last_update(event: models.StatusReceivedEvent):
    last_update['text'] = f"Last Update: {event.timestamp.strftime(TIME_FORMAT)}"
    update_action()


start_button.config(command=async_handler(start))
stop_button.config(command=async_handler(stop))

start_button.pack()
stop_button.pack()
status_label.pack()
last_update.pack()
last_status.pack()
actions_list.pack(fill="both", expand="yes")

if __name__ == '__main__':
    async_mainloop(root)
