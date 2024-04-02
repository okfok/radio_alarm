import asyncio

import models
from logs import logger

conf: models.ConfigModel = None

loop = asyncio.new_event_loop()


def load_conf():
    global conf
    logger.debug("Loading config file")
    try:
        with open('conf.json', 'r') as f:
            conf = models.ConfigModel.parse_raw(f.read())

    except FileNotFoundError as err:
        logger.error("Config file not found! Generating template.")
        conf = models.ConfigModel()
        with open('conf.json', 'w') as f:
            f.write(conf.model_dump_json())
        logger.debug("Config file generated. Exiting.")
        raise err
    logger.debug("Loaded successfully")


def save_conf():
    with open('conf.json', 'w') as f:
        f.write(conf.model_dump_json())


class Status:
    def __init__(self):
        logger.debug("Loading status file")
        try:
            with open('status.json', 'r') as f:
                self.model = models.StatusModel.parse_raw(f.read())
        except FileNotFoundError:
            logger.warning("Status file generated.")
            self.model = models.StatusModel()

    def save(self):
        logger.debug("Saving status file")
        with open('status.json', 'w') as f:
            f.write(self.model.model_dump_json())
