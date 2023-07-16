import logging
import os
import sys


def get_logger(level=logging.DEBUG, log_file=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    if not check_existing_handler(handler, logger.handlers):
        logger.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        if not check_existing_handler(file_handler, logger.handlers):
            logger.addHandler(file_handler)
            logger.info(f'Logging to file: {log_file}')

    return logger


def check_existing_handler(new_handler, existing_handlers):
    for handler in existing_handlers:
        if handler.stream == new_handler.stream:
            return True

    return False
