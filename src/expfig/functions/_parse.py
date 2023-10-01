import argparse
from ast import literal_eval


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def str2none(v):
    if v == 'null':
        return None
    return v


class ListType:
    __name__ = 'ListType'
    # TODO (ahalev) make this a metaclass, inherit from type and deprecate this class attr

    def __init__(self, _type):
        self.type = _type

    def __call__(self, value):
        if isinstance(value, list):
            literal = value
        elif self.type == str2none:
            literal = self.str2none_eval(value)
        else:
            try:
                return self.type(value)
            except ValueError:
                literal = literal_eval(value)

        return self.type_check(literal)

    def type_check(self, value):
        if isinstance(value, list) and all(isinstance(v, self.types_to_check) for v in value) or \
                isinstance(value, self.types_to_check):
            return value

        raise argparse.ArgumentTypeError(f'Invalid value(s) for type {self.type}: {value}')

    @property
    def types_to_check(self):
        if self.type == str2none:
            return str, type(None)

        return self.type


    @staticmethod
    def str2none_eval(value):
        if value.startswith('[') and value.endswith(']'):
            _value = literal_eval(value)
            return [str2none(v) for v in _value]

        return str2none(value)


class ListAction(argparse._StoreAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 1 and isinstance(values[0], list) and self.type.type != list:
            values = values[0]

        return super().__call__(parser, namespace, values, option_string=None)
