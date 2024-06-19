import pytest
import yaml

from expfig.core._parse_yaml_obj import YamlType
from tests.helpers.yaml_obj import InsuranceA


class TestYamlType:
    def test_yaml_default_is_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        loaded = yaml_type('!InsuranceA {value: 10}')

        assert isinstance(loaded, InsuranceA)
        assert loaded.value == 10

    def test_yaml_default_is_not_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        with pytest.raises(yaml.YAMLError):
            _ = yaml_type('abcd')

    def test_yaml_default_is_bad_yaml(self):
        yaml_type = YamlType(yaml_default=True)

        with pytest.raises(yaml.YAMLError):
            _ = yaml_type('!MisspelledInsurance {value: 10}')
