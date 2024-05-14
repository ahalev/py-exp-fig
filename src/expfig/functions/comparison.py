from expfig import Namespacify
from expfig.utils.get_pandas import pandas as pd
from expfig.utils.api import is_dict_like


def compare(ns, base=None):
    """
    Parameters
    ----------
    ns: dict or list-like of Namespacify or path-like.
        Either Namespacifys to compare or paths to yaml files to load namespacifys from.
    base: Namespacify, path-like or None, default None.
        Base namespacify to compare to. If None, only pairwise comparisons are performed. Otherwise, both pairwise and
        comparisons to the base are performed.

    Returns
    -------

    """
    if base is not None:
        base = _load_if_necessary(base)

    if not is_dict_like(ns):
        ns = dict(enumerate(ns))

    ns = {str(k): _load_if_necessary(v) for k, v in ns.items()}

    pairwise_diffs = {}
    for name, namespace in ns.items():
        diffs = []
        if base is not None:
            diffs.append(namespace.difference(base).to_series())

        diffs.extend(namespace.difference(other_namespace).to_series() for other_namespace in ns.values())
        pairwise_diffs[name] = pd.concat(diffs).drop_duplicates()

    return pd.concat(pairwise_diffs, axis=1).sort_index()


def _load_if_necessary(value):
    if isinstance(value, Namespacify):
        return value

    return Namespacify.from_yaml(value)
