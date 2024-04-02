import sys

import events
import logs
import core


def init():
    logs.init_logger(('-debug' in sys.argv))
    logs.logger.info("Starting")
    core.load_conf()

    core.loop.run_until_complete(events.mainloop())


if __name__ == '__main__':
    init()
