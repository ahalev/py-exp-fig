import yaml

from collections import UserDict
from logging import getLogger

from .logger import make_sequential_log_dir

yaml.SafeDumper.add_multi_representer(UserDict, yaml.SafeDumper.represent_dict)
logger = getLogger(__name__)


class Namespacify(UserDict):
    def __init__(self, in_dict, name=''):
        self.name = name

        in_dict = in_dict.copy()

        for key in in_dict.keys():
            if key == 'name':
                raise NameError(f"Cannot use key 'name'.")
            if isinstance(in_dict[key], dict):
                in_dict[key] = Namespacify(in_dict[key], name=key)

        super().__init__(in_dict)

    def with_name_from_keys(self, *keys, prefix='', suffix='', uppercase=True):
        if not keys:
            obj = ''
        else:
            obj = self
            for j, key in enumerate(keys):
                try:
                    obj = obj[key]
                except (KeyError, TypeError):
                    raise KeyError(f'Nested value {"->".join(keys[:j])} does not exist.')

            if isinstance(obj, (dict, UserDict)):
                raise KeyError(f'Nested value {"->".join(keys)} is dict-like, should be str, int, etc.')

            if uppercase:
                obj = obj.upper()

        self.name = f'{prefix}{obj}{suffix}'

        return self

    def update(self, *args, **kwargs):
        return nested_dict_update(self, *args, nest_namespacify=True, **kwargs)

    def pprint(self, indent=0):
        name = self.name if self.name else 'config'
        print("{}{}:".format(' ' * indent, name))

        indent += 4

        for k, v in self.items():
            if k == "name":
                continue
            if isinstance(v, Namespacify):
                v.pprint(indent)
            else:
                print("{}{}: {}".format(' ' * indent, k, v))

    def to_dict(self):
        return {k: v.to_dict() if isinstance(v, Namespacify) else (v.copy() if hasattr(v, 'copy') else v)
                for k, v in self.items()}

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

    def __dir__(self):
        rv = set(super().__dir__())
        rv = rv | set(self.keys())
        return sorted(rv)

    def __getattr__(self, item):
        if item == 'data':
            raise RuntimeError('Attempting to access self.data before initialization.')
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)

    def intersection(self, other):
        intersection = {}

        for k, v in self.items():
            if k in other:
                if other[k] == v:
                    intersection[k] = v
                elif isinstance(v, Namespacify) and isinstance(other[k], Namespacify):
                    subint = v.intersection(other[k])
                    if subint:
                        intersection[k] = subint

        return intersection

    def __xor__(self, other):
        diff = {}

        keys = {*self.keys(), *other.keys()}
        for k in keys:
            if k not in self:
                diff[k] = other[k]
                continue

            elif k not in other:
                diff[k] = self[k]
                continue

            elif self[k] != other[k]:
                if isinstance(self[k], Namespacify):
                    diff[k] = self[k].__xor__(other[k])
                else:
                    diff[k] = self[k]

        return Namespacify(diff, name=self.name)

    def __and__(self, other):
        return self.intersection(other)

    def __deepcopy__(self, memo=None):
        return Namespacify(self.to_dict(), self.name)


def nested_dict_update(nested_dict, *args, nest_namespacify=False, **kwargs):
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
                nested_dict[k].update(v)
            else:
                nested_dict[k] = Namespacify(v, name=k) if nest_namespacify else v
        else:
            nested_dict[k] = v

    return nested_dict
