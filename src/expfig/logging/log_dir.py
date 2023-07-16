import os
import tempfile
from expfig.logging import get_logger


def make_sequential_log_dir(log_dir, subdirs=(), use_existing_dir=False, logger_file=None, logging_level=10):
    """Taken from rlworkgroup/garage.

    Creates log_dir, appending a number if necessary.

    Attempts to create the directory `log_dir`. If it already exists, appends
    "_1". If that already exists, appends "_2" instead, etc.

    If `logger_file` is not None, a logger will be created that logs to the file `logger_file` in the created `log_dir`.
    This logger can be accessed by calling `expfig.logging.get_logger().

    Args:
        log_dir (str or None): The log directory to attempt to create. If None, logs to a temporary directory
        subdirs (list of str): subdirectories to create in the log_dir directory.
        use_existing_dir (bool): whether to simply return the dir if it exists (will log to existing dir).
        logger_file (str or None): If not None, creates a logger that logs to this file within the log_dir.
        logging_level: (int or str): Level for the logger, e.g. `INFO`. See python Logging module for more info.

    Returns:
        str: The log directory created.

    """

    if log_dir is None:
        log_dir = tempfile.mkdtemp()

    i = 0
    while True:
        try:
            if i == 0:
                os.makedirs(log_dir)
            else:
                possible_log_dir = '{}_{}'.format(log_dir, i)
                os.makedirs(possible_log_dir)
                log_dir = possible_log_dir

            break

        except FileExistsError:
            if use_existing_dir:
                break

            i += 1

    for subdir in subdirs:
        os.makedirs(os.path.join(log_dir, subdir), exist_ok=True)

    if logger_file:
        logger = get_logger(level=logging_level, log_file=os.path.join(log_dir, logger_file))
        return log_dir

    return log_dir
