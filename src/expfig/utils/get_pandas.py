class BadPandas:
    def __getattr__(self, item):
        if item.startswith('__'):
            # Alleviates pytest issue with self.__unwrapped__, see https://github.com/pytest-dev/pytest/issues/5080
            raise AttributeError(item)

        raise ModuleNotFoundError("Optional dependency 'pandas' not installed. "
                                  "Install with 'pip install pandas' to utilize this functionality.")


def _get_pandas():
    try:
        import pandas as pd
    except ImportError:
        return BadPandas()
    else:
        return pd


pandas = _get_pandas()
