import argparse

from ast import literal_eval
from warnings import warn

from expfig.core import str2bool, str2none, TypeToNone
from expfig.core._parse_yaml_obj import YamlType
from expfig.utils import api


def parse_arg_type(arg_name, base_default):
    additional_args = {}

    if api.is_list_like(base_default):
        additional_args.update(nargs='+', action=ListAction)
        _type = ListType.from_list(base_default, arg_name)

    elif getattr(base_default, 'yaml_tag', None) is not None:  # is a Yaml object
        _type = YamlType(yaml_default=True)
    elif base_default is None or base_default == '': # allow empty strings to be yaml-objects but no failure if not
        _type = YamlType(yaml_default=False)
    else:
        _type = type(base_default)

    if _type == bool:
        _type = str2bool
    elif _type == str:
        _type = str2none

    return _type, additional_args


class ListType:
    __name__ = 'ListType'
    # TODO (ahalev) make this a metaclass, inherit from type and deprecate this class attr

    def __init__(self, _type):
        self._type = TypeToNone(_type)

    def __call__(self, value):
        if isinstance(value, list):
            literal = [self._type(v) for v in value]
        elif self._type.type == str:
            literal = self.str2none_eval(value)
        else:
            try:
                return self._type(value)
            except ValueError:
                literal = literal_eval(value)
                return self(literal)

        return self.type_check(literal)

    def type_check(self, value):
        if isinstance(value, list) and all(isinstance(v, self.valid_types) for v in value) or \
                isinstance(value, self.valid_types):
            return value

        raise argparse.ArgumentTypeError(f'Invalid value(s) for type {self._type}: {value}')

    @property
    def valid_types(self):
        return self._type.valid_types

    @property
    def type(self):
        return self._type.type

    @staticmethod
    def str2none_eval(value):
        if value.startswith('[') and value.endswith(']'):
            _value = literal_eval(value)
            return [str2none(v) for v in _value]

        return str2none(value)

    @classmethod
    def from_list(cls, list_like, arg_name=None):
        unique_types = {type(x) for x in list_like if x is not None}

        if len(unique_types) == 1:
            _type = unique_types.pop()
        else:
            _type = str

            if len(unique_types):
                arg = f"'{arg_name}' " if arg_name else ""
                warn(f"Collecting list-like argument {arg}with non-unique types {unique_types} in default value "
                     "Collected values will be str.")

        return cls(_type)


class ListAction(argparse._StoreAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 1 and isinstance(values[0], list) and self.type.type != list:
            values = values[0]

        return super().__call__(parser, namespace, values, option_string=None)


def get_type(type_obj):
    try:
        return type_obj.type.__name__
    except AttributeError:
        return type_obj.__name__
