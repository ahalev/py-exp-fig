import yaml

from functools import reduce

from expfig.functions._str_types import str2none


CMD_LINE_YAML_REPLACEMENTS = [('{', '{ '), (':', ': ')]


class YamlType:
    __name__ = 'YamlType'

    def __init__(self, yaml_default):
        self.yaml_default = yaml_default

    def __call__(self, value):
        if self.yaml_default:
            return _load_yaml_value(value)
        elif is_yaml_str(value):  # try to load yaml but if not no worries, just return value
            try:
                return _load_yaml_value(value)
            except yaml.YAMLError:
                pass

        return str2none(value)


def is_yaml_str(value):
    return isinstance(value, str) and value.startswith('!')


def _load_yaml_value(value):
    try:
        value = yaml.safe_load(value)
    except yaml.YAMLError:
        try:
            value = yaml.safe_load(f'{value} {{}}')
        except yaml.YAMLError:
            value = reduce(lambda _str, kv: _str.replace(*kv), CMD_LINE_YAML_REPLACEMENTS, value)
            value = yaml.safe_load(value)

    return value
