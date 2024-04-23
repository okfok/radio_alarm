import sys

import core
import events
import logs
import utils


def init():
    if '-c' in sys.argv:
        utils.console_command(*sys.argv[sys.argv.index('-c') + 1:])
        return
    logs.init_logger(('--debug' in sys.argv or '-d' in sys.argv))
    logs.logger.info("Starting")
    core.Config.load()

    if '--reload-conf' in sys.argv:
        core.Config.save()


if __name__ == '__main__':
    init()
    logs.logger.info("Mainloop enter")
    try:
        core.loop.run_until_complete(events.mainloop())
    finally:
        logs.logger.info("Mainloop exit")
