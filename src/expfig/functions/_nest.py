import functools
import pandas as pd
from collections import UserDict


def nest(arguments, delimiter='.'):
    if set(arguments.keys()) == {''}:
        return arguments['']

    restructured = {}
    for key, value in arguments.items():
        top_key, _, bottom_keys = key.partition(delimiter)
        update_with = {top_key: nest({bottom_keys: value})}
        nested_dict_update(restructured, update_with)

    return restructured


def unnest(nested, delimiter='.', _key_stack=''):
    flat = {}
    for k, v in nested.items():
        flat_key = delimiter.join([_key_stack, k]) if _key_stack else k
        if pd.api.types.is_dict_like(v):
            flat.update(unnest(v, delimiter, flat_key))
        else:
            flat[flat_key] = v

    return flat


def depth(d):
    if pd.api.types.is_dict_like(d):
        return 1 + (max(map(depth, d.values())) if d else 0)
    return 0


def nested_dict_update(nested_dict, *args, nest_namespacify=False, **kwargs):
    from expfig import Namespacify  # prevent circular import

    if args:
        if len(args) != 1 or not isinstance(args[0], (dict, UserDict)):
            raise TypeError('Invalid arguments')
        elif kwargs:
            raise TypeError('Cannot pass both args and kwargs.')

        d = args[0]
    else:
        d = kwargs

    for k, v in d.items():
        if isinstance(v, (dict, UserDict)):
            if k in nested_dict:
                nested_dict_update(
                    nested_dict[k], v, nest_namespacify=(nest_namespacify or isinstance(nested_dict[k], Namespacify))
                )
            else:
                nested_dict[k] = Namespacify(v) if nest_namespacify else v
        else:
            nested_dict[k] = v

    return nested_dict
