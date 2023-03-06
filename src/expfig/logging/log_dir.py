import os


def make_sequential_log_dir(log_dir, subdirs=(), use_existing_dir=False):
    """Taken from rlworkgroup/garage.

    Creates log_dir, appending a number if necessary.

    Attempts to create the directory `log_dir`. If it already exists, appends
    "_1". If that already exists, appends "_2" instead, etc.

    Args:
        log_dir (str): The log directory to attempt to create.
        subdirs (list of str): subdirectories to create in the log_dir directory.
        use_existing_dir (bool): whether to simply return the dir if it exists (will log to existing dir).

    Returns:
        str: The log directory actually created.

    """
    i = 0
    while True:
        try:
            if i == 0:
                os.makedirs(log_dir)
            else:
                possible_log_dir = '{}_{}'.format(log_dir, i)
                os.makedirs(possible_log_dir)
                log_dir = possible_log_dir

            for subdir in subdirs:
                os.makedirs(os.path.join(log_dir, subdir))

            return log_dir

        except FileExistsError:
            if use_existing_dir:

                for subdir in subdirs:
                    os.makedirs(os.path.join(log_dir, subdir), exist_ok=True)

                return log_dir

            i += 1
