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
    def __init__(self, _type):
        self.type = _type

    def __call__(self, value):
        if self.type == str:
            literal = self.str_eval(value)
        else:
            try:
                return self.type(value)
            except ValueError:
                literal = literal_eval(value)

        if all(isinstance(v, self.type) for v in literal):
            return literal

        raise argparse.ArgumentTypeError(f'Invalid value(s) for type {self.type}: {value}')

    @staticmethod
    def str_eval(value):
        if value.startswith('[') and value.endswith(']'):
            return literal_eval(value)

        return value


class ListAction(argparse._StoreAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) == 1 and isinstance(values[0], list) and self.type.type != list:
            values = values[0]

        return super().__call__(parser, namespace, values, option_string=None)
