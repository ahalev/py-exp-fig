import pytest
import yaml

from expfig.core._parse_yaml_obj import YamlType


class AYamlObject(yaml.YAMLObject):
    yaml_dumper = yaml.SafeDumper
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!AYamlObject'

    def __init__(self, value):
        self.value = value


class TestYamlType:
    def test_yaml_default_is_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        loaded = yaml_type('!AYamlObject {value: 10}')

        assert isinstance(loaded, AYamlObject)
        assert loaded.value == 10

    def test_yaml_default_is_not_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        with pytest.raises(yaml.YAMLError):
            _ = yaml_type('abcd')

    def test_yaml_default_is_bad_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        with pytest.raises(yaml.YAMLError):
            _ = yaml_type('!MisspelledYamlObject {value: 10}')
