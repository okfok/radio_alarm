import core
import logs
import funcs

if __name__ == '__main__':
    core.init()
    logs.logger.info("Mainloop enter")
    try:
        core.loop.run_until_complete(funcs.mainloop())
    finally:
        logs.logger.info("Mainloop exit")
