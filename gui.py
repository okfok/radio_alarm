import asyncio
import os
import sys
import tkinter as tk

import pystray
from PIL import Image, ImageTk
from async_tkinter_loop import async_handler, async_mainloop
from tzlocal import get_localzone

import core
import events
import logs
import models
from radio_alarm import init


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


TIME_FORMAT = '%H:%M:%S %d.%m'

init()

root = tk.Tk()
root.title('Radio Alarm')
root.geometry('250x150')
root.resizable(False, False)

ico = Image.open(resource_path("favicon.ico"))

root.wm_iconphoto(True, ImageTk.PhotoImage(ico))

loop = asyncio.get_event_loop()


async def mainloop():
    try:
        await events.mainloop()
    except asyncio.CancelledError:
        ...


mainloop_task = None

last_update = tk.Label(root, text="Last Update: ")
last_status = tk.Label(root, text="Last Status: ")
status_label = tk.Label(root, text="Status: off", fg='#00f')
start_button = tk.Button(root, text="Start")
stop_button = tk.Button(root, text="Stop", state='disabled')


async def start():
    start_button['state'] = 'disabled'
    stop_button['state'] = 'normal'

    global mainloop_task
    mainloop_task = loop.create_task(events.mainloop())

    logs.logger.info("Mainloop enter")

    try:
        await asyncio.gather(mainloop_task)
    except asyncio.CancelledError:
        pass
    finally:
        logs.logger.info("Mainloop exit")
        stop_button['state'] = 'disabled'
        start_button['state'] = 'normal'
        status_label['text'] = 'Status: off'
        status_label['fg'] = '#00f'


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


start_button.config(command=async_handler(start))
stop_button.config(command=async_handler(stop))

start_button.pack()
stop_button.pack()
status_label.pack()
last_update.pack()
last_status.pack()


# Define a function for quit the window
def quit_window(icon, item):
    icon.stop()
    root.destroy()


# Define a function to show the window again
def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)


# Hide the window and show on the system taskbar
def hide_window():
    root.withdraw()
    menu = (
        pystray.MenuItem('Show', show_window),
        pystray.MenuItem('Quit', quit_window),
    )
    icon = pystray.Icon("name", ico, "Radio Alarm", menu)
    icon.run()


root.protocol('WM_DELETE_WINDOW', hide_window)

if __name__ == '__main__':
    async_mainloop(root)
