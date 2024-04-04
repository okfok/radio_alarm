import sys

import events
import logs
import core
import utils


def init():
    if '-c' in sys.argv:
        utils.console_command(*sys.argv[sys.argv.index('-c') + 1:])
        return
    logs.init_logger(('-debug' in sys.argv))
    logs.logger.info("Starting")
    core.load_conf()

    if '-reload-conf' in sys.argv:
        core.save_conf()

    core.loop.run_until_complete(events.mainloop())


if __name__ == '__main__':
    init()
