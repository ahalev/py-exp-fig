import contextlib
import enum
import functools
import logging
import os
import sys


def get_logger(level=logging.DEBUG, log_file=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    formatter = ColorFormatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

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
            logger.info(f'Logging to file: {os.path.abspath(log_file)}')

    return logger

class ColorFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formats = Formats.level_formats(self._style._fmt)

    def format(self, record: logging.LogRecord) -> str:
        with self.push_format(record.levelno):
            return super().format(record)

    @contextlib.contextmanager
    def push_format(self, level):
        old_fmt = self._style._fmt
        self._style._fmt = self.formats[level]

        try:
            yield
        finally:
            self._style._fmt = old_fmt


class Formats(enum.Enum):
    GRAY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    LEVELS = {
        logging.DEBUG: GRAY,
        logging.INFO: GRAY,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED
    }

    @classmethod
    def level_formats(cls, format_str):
        return {level: cls.format(format_str, color) for level, color in cls.LEVELS.value.items()}

    @classmethod
    def format(cls, format_str, color):
        return ''.join([color, format_str, cls.RESET.value])


def check_existing_handler(new_handler, existing_handlers):
    for handler in existing_handlers:
        if handler.stream == new_handler.stream:
            return True

    return False
