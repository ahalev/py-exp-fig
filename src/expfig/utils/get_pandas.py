class BadPandas:
    def __getattr__(self, item):
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
