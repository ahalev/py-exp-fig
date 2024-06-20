import argparse

from ast import literal_eval

def _str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


class TypeToNone:
    def __init__(self, _type):
        self.type = _type

    def __call__(self, v):
        if v in (None, 'None', 'null'):
            return None
        return self.type(v)

    def __repr__(self):
        return f'TypeToNone({repr(self.type)})'

    def __eq__(self, other):
        if isinstance(self, type(other)) or isinstance(other, type(self)):
            return self.type == other.type

        return NotImplemented

    def __hash__(self):
        return hash(self.type)

    @property
    def valid_types(self):
        return self.type, type(None)


class _None2Any(TypeToNone):
    def __init__(self):
        super().__init__('any')

    def __call__(self, v):
        return self.any_item(v)

    @staticmethod
    def any_item(v):
        if v in (None, 'None', 'null'):
            return None
        elif isinstance(v, str):
            v = v.replace('null', 'None')
            try:
                return literal_eval(v)
            except (ValueError, SyntaxError):
                pass

        return v

    @property
    def valid_types(self):
        return str, int, float, list, dict, set, bool, tuple, type(None)


class _Str2Bool(TypeToNone):
    def __init__(self):
        super().__init__(bool)

    def __call__(self, v):
        if v in (None, 'None', 'null'):
            return None

        return _str2bool(v)


none2any = _None2Any()
str2bool = _Str2Bool()
str2none = TypeToNone(str)
