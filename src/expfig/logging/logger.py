import logging
import sys


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
