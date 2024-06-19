import yaml


class InsuranceA(yaml.YAMLObject):
    yaml_dumper = yaml.SafeDumper
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!InsuranceA'

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented

        return self.value == other.value


class InsuranceB(yaml.YAMLObject):
    yaml_dumper = yaml.SafeDumper
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!InsuranceB'

    def __init__(self, a=None, b=None):
        self.a = a
        self.b = b

    def to_dict(self):
        return {
            'a': self.a,
            'b': self.b,
            'c': 'c'
        }

    def __eq__(self, other):
        if type(self) != type(other):
            return NotImplemented

        return self.a == other.a and self.b == other.b
