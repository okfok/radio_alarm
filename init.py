import datetime
import logging
import events

import core


def init():
    logging.basicConfig(filename='info.log', level=logging.INFO)
    logging.info(f"Starting {datetime.datetime.now()}")
    core.load_conf()

    core.loop.run_until_complete(events.mainloop())


if __name__ == '__main__':
    init()
