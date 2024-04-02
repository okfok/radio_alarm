import logging

logger = logging.getLogger('radio_alarm')


def init_logger(debug: bool = False):
    global logger
    logger.setLevel(1)

    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

    info_file_handler = logging.FileHandler('info.log')
    info_file_handler.setFormatter(formatter)
    info_file_handler.setLevel(logging.INFO)

    logger.addHandler(info_file_handler)

    if debug:
        debug_file_handler = logging.FileHandler('debug.log')
        debug_file_handler.setFormatter(formatter)
        debug_file_handler.setLevel(logging.DEBUG)

        logger.addHandler(debug_file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    logger.addHandler(stream_handler)
