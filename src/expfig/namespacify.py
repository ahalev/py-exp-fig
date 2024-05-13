import functools

import numpy as np
import yaml

from contextlib import contextmanager
from collections import UserDict
from logging import getLogger

from . import nested_dict_update
from .core import depth, flatten
from .logging import make_sequential_log_dir

from expfig.utils.api import is_dict_like
from expfig.utils.get_pandas import pandas as pd


yaml.SafeDumper.add_multi_representer(UserDict, yaml.SafeDumper.represent_dict)
logger = getLogger(__name__)

class Namespacify(UserDict):
    def __init__(self, in_dict):
        super().__init__(in_dict)

    def update(self, *args, **kwargs):
        return nested_dict_update(self, *args, nest_namespacify=True, **kwargs)

    def pprint(self, indent=0, log_func=None, _recur=False):
        with repr_as_default_yaml_representer():
            str_out = yaml.safe_dump(self)

        if indent:
            pref = '\t'*indent
            str_out = str_out.replace('\n', '\n' + pref)
            str_out = pref + str_out

        if log_func is not None:
            log_func(str_out)
        else:
            print(str_out)

        return str_out

    def depth(self):
        return depth(self)

    def to_dict(self):
        return {k: v.to_dict() if isinstance(v, Namespacify) else (v.copy() if hasattr(v, 'copy') else v)
                for k, v in self.items()}

    def to_series(self):
        series = pd.json_normalize(self.to_dict()).squeeze()

        try:
            series.index = pd.MultiIndex.from_tuples([x.split('.') for x in series.index])
        except TypeError:
            if not series.empty:
                raise

        return series

    def flatten(self, delimiter='.', levels=None):
        return flatten(self, delimiter=delimiter, levels=levels)

    def intersection(self, other):
        intersection = {}

        for k, v in self.items():
            if k in other:
                if equal(other[k], v):
                    intersection[k] = v
                elif isinstance(v, Namespacify) and isinstance(other[k], Namespacify):
                    subint = v.intersection(other[k])
                    if subint:
                        intersection[k] = subint

        return Namespacify(intersection)

    def symmetric_difference(self, other):
        """
        Get all values that differ in ``self`` or ``other``.

        Returns the value in ``self`` if it exists and differs from ``other``. Otherwise returns the value in ``other``.

        If ``self['a'] = 1`` and ``other['a'] = 2``, ``self.symmetric_difference(other)['a'] = 1``.
        If ``self['a'] = 1`` and ``'a' not in other``, `self.symmetric_difference(other)['a'] = 1``.
        If ``'a' not in self`` and ``other['a'] = 2``, `self.symmetric_difference(other)['a'] = 2``.


        Parameters
        ----------
        other : dict-like
            Object to compare against

        Returns
        -------
        difference : :class:`.Namespacify`
            Difference between ``self`` and ``other``.

        """

        diff = {}

        if type(self) != type(other):
            return self.copy()

        keys = {*self.keys(), *other.keys()}
        for k in keys:
            if k not in self:
                diff[k] = other[k]
                continue

            elif k not in other:
                diff[k] = self[k]
                continue

            elif not equal(self[k], other[k]):
                if isinstance(self[k], Namespacify):
                    diff[k] = self[k].symmetric_difference(other[k])
                else:
                    diff[k] = self[k]

        return Namespacify(diff)

    def difference(self, other):
        """
        Get all values that are in ``self`` that are NOT (or are different) in ``other``.

        If ``self['a'] = 1`` and ``other['a'] = 2``, ``self.difference(other)['a'] = 1``.
        If ``a not in self`` and ``other['a'] = 2``, ``self.difference(other)['a']`` returns a ``KeyError``.

        Parameters
        ----------
        other : dict-like
            Object to compare against

        Returns
        -------
        difference : :class:`.Namespacify`
            Difference between ``self`` and ``other``.

        """
        diff = {}
        for k, v in self.items():
            if not is_dict_like(other):
                diff[k] = v
            elif k not in other:
                diff[k] = v
            elif not equal(v, other[k]):
                if isinstance(v, Namespacify):
                    diff[k] = v.difference(other[k])
                else:
                    diff[k] = v

        return Namespacify(diff)

    def serialize(self, stream=None):
        return yaml.safe_dump(self, stream=stream)

    def serialize_to_dir(self, log_dir, fname='namespacify.yaml', use_existing_dir=False):
        log_dir = make_sequential_log_dir(log_dir, use_existing_dir=use_existing_dir)
        log_file = f'{log_dir}/{fname}'

        with open(log_file, 'w') as f:
            self.serialize(f)

        logger.info(f'Logged {type(self).__name__} to {log_file}')

        return log_dir

    @classmethod
    def deserialize(cls, stream):
        return cls(yaml.safe_load(stream))

    @classmethod
    def from_yaml(cls, filepath):
        with open(filepath, 'r') as stream:
            return cls.deserialize(stream)

    def __dir__(self):
        rv = set(super().__dir__())

        try:
            rv = rv | set(self.keys())
        except RuntimeError:
            pass

        return sorted(rv)

    def __getitem__(self, item):
        if item[0] == slice(None) or isinstance(item[0], list):
            keys = self.keys() if item[0] == slice(None) else item[0]
            return {k: self[k][item[1:]] for k in keys}

        elif isinstance(item, tuple):
            out = self[item[0]]
            if len(item) == 1:
                return out
            try:
                return out[item[1:]]
            except TypeError:  # out is not subscriptable, raise KeyError
                raise KeyError(f"'{item[1:]}', item of type '{type(out).__name__}' is not subscriptable")

        return super().__getitem__(item)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            nested_update = functools.reduce(lambda val, k: {k: val}, reversed(key), value)
            nested_dict_update(self, nested_update, nest_namespacify=True)

        elif isinstance(value, dict):
            nested_dict_update(self, {key: value}, nest_namespacify=True)

        else:
            super().__setitem__(key, value)


    def __getattr__(self, item):
        if item == 'data':
            raise RuntimeError('Attempting to access self.data before initialization.')
        try:
            return self[item]
        except (KeyError, RuntimeError):
            raise AttributeError(item)

    def __setattr__(self, key, value):
        try:
            contains_key = key in self
        except RuntimeError:
            pass
        else:
            if contains_key:
                self[key] = value
                return

        super().__setattr__(key, value)

    def __xor__(self, other):
        return self.symmetric_difference(other)

    def __and__(self, other):
        return self.intersection(other)

    def __sub__(self, other):
        return self.difference(other)

    def __deepcopy__(self, memo=None):
        return Namespacify(self.to_dict())


def equal(a, b):
    try:
        return bool(a == b)
    except ValueError:
        return np.array_equal(a, b)


@contextmanager
def repr_as_default_yaml_representer():
    def default_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', repr(data))

    yaml.representer.SafeRepresenter.add_representer(None, default_representer)

    try:
        yield
    finally:
        yaml.representer.SafeRepresenter.yaml_representers.pop(None)
