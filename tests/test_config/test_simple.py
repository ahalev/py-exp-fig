import argparse
import contextlib
import os
import sys
import pytest
import tempfile as _tempfile
import yaml

from unittest import mock
from expfig import Config

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2,
    'insured': True,
    'lease': False,
}

LIST_CONTENTS = {
    **CONTENTS,
    'brands': ['toyota']
}

NESTED_CONTENTS = {
    'jeep': CONTENTS,
    'truck': {
        'car': 'skirt',
        'wheels': 18,
        'axles': 6
    },
    'dealer': 'michael-jordan-nissan'
}


def mock_sys_argv(*args):
    return mock.patch.object(sys, 'argv', [sys.argv[0], *args])


class TestSimpleConfig:

    def test_dashed_key_exception(self):
        default = {'car-brand': 'yoda', **CONTENTS}
        with pytest.raises(NameError, match="Invalid character '-' in key 'car-brand'"):
            _ = Config(default=default)

    @mock_sys_argv()
    def test_no_argv(self):
        config = Config(default=CONTENTS)

        assert config.car == 'vroom'
        assert config.wheels == 4
        assert config.axles == 2

    @mock_sys_argv('--car', 'skirt')
    def test_single_argv(self):
        config = Config(default=CONTENTS)
        assert config.car == 'skirt'

    @mock_sys_argv('--dealer', 'michael-jordan-toyota', '--truck.car', 'bing')
    def test_nested_argv(self):
        config = Config(default=NESTED_CONTENTS)

        assert config.dealer == 'michael-jordan-toyota'
        assert config.truck.car == 'bing'

    def test_config_file(self):
        yaml_dump = {'dealer': 'michael-jordan-toyota'}

        with tempfile(suffix='.yaml', mode='w') as temp_yaml, mock_sys_argv('--config', temp_yaml.name):
            yaml.safe_dump(yaml_dump, temp_yaml)
            config = Config(default=NESTED_CONTENTS)

            assert config.dealer == 'michael-jordan-toyota'
            assert config.truck.car == 'skirt'

    def test_multiple_config_file_non_overlap(self):
        yaml_dump_1 = {'dealer': 'michael-jordan-toyota'}
        yaml_dump_2 = {'truck': {'axles': 128}}

        with tempfile(suffix='.yaml', mode='w') as temp_yaml_1,\
                tempfile(suffix='.yaml', mode='w') as temp_yaml_2, \
                mock_sys_argv('--config', temp_yaml_1.name, temp_yaml_2.name):

            yaml.safe_dump(yaml_dump_1, temp_yaml_1)
            yaml.safe_dump(yaml_dump_2, temp_yaml_2)

            config = Config(default=NESTED_CONTENTS)

            assert config.dealer == 'michael-jordan-toyota'
            assert config.truck.axles == 128
            assert config.truck.car == 'skirt'

    def test_multiple_config_file_overlap(self):
        yaml_dump_1 = {'dealer': 'michael-jordan-toyota'}
        yaml_dump_2 = {'truck': {'axles': 128}, 'dealer': 'michael-jordan-honda'}

        with tempfile(suffix='.yaml', mode='w') as temp_yaml_1,\
                tempfile(suffix='.yaml', mode='w') as temp_yaml_2, \
                mock_sys_argv('--config', temp_yaml_1.name, temp_yaml_2.name):

            yaml.safe_dump(yaml_dump_1, temp_yaml_1)
            yaml.safe_dump(yaml_dump_2, temp_yaml_2)

            config = Config(default=NESTED_CONTENTS)

            assert config.dealer == 'michael-jordan-honda'
            assert config.truck.axles == 128
            assert config.truck.car == 'skirt'

    def test_config_file_explicit_arg_overlap(self):
        yaml_dump = {'truck': {'axles': 128}, 'dealer': 'michael-jordan-toyota'}

        with tempfile(suffix='.yaml', mode='w') as temp_yaml, \
                mock_sys_argv('--config', temp_yaml.name, '--dealer', 'michael-jordan-honda'):

            yaml.safe_dump(yaml_dump, temp_yaml)

            config = Config(default=NESTED_CONTENTS)

            assert config.dealer == 'michael-jordan-honda'
            assert config.truck.axles == 128
            assert config.truck.car == 'skirt'

    def test_config_file_explicit_arg_overlap_order_swap(self):
        yaml_dump = {'truck': {'axles': 128}, 'dealer': 'michael-jordan-toyota'}

        with tempfile(suffix='.yaml', mode='w') as temp_yaml, \
                mock_sys_argv('--dealer', 'michael-jordan-honda', '--config', temp_yaml.name):

            yaml.safe_dump(yaml_dump, temp_yaml)

            config = Config(default=NESTED_CONTENTS)

            assert config.dealer == 'michael-jordan-honda'
            assert config.truck.axles == 128
            assert config.truck.car == 'skirt'

    @mock_sys_argv('--truck.car', 'null')
    def test_null_read(self):
        config = Config(default=NESTED_CONTENTS)

        assert config.truck.car is None

    @pytest.mark.parametrize('true_val', ['yes', 'true', 't', 'y', '1'])
    def test_true_reads_original_true(self, true_val):

        with mock_sys_argv('--insured', true_val):
            config = Config(default=CONTENTS)

        assert config.insured

    @pytest.mark.parametrize('true_val', ['yes', 'true', 't', 'y', '1'])
    def test_true_reads_original_false(self, true_val):

        with mock_sys_argv('--lease', true_val):
            config = Config(default=CONTENTS)

        assert config.lease

    @pytest.mark.parametrize('false_val', ['no', 'false', 'f', 'n', '0'])
    def test_false_reads_original_true(self, false_val):

        with mock_sys_argv('--insured', false_val):
            config = Config(default=CONTENTS)

        assert not config.insured

    @pytest.mark.parametrize('false_val', ['no', 'false', 'f', 'n', '0'])
    def test_false_reads_original_false(self, false_val):

        with mock_sys_argv('--lease', false_val):
            config = Config(default=CONTENTS)

        assert not config.lease

    @mock_sys_argv('--insured', 'not-bool')
    def test_bool_fail(self):

        with pytest.raises(SystemExit):
            _ = Config(default=CONTENTS)


class TestListRead:
    # Test reading lists from the command line

    @mock_sys_argv()
    def test_no_args(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota']

    @mock_sys_argv('--brands', 'toyota', 'honda')
    def test_separate_args(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', 'honda']

    @mock_sys_argv('--brands', '[]')
    def test_explicit_list(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == []

    @mock_sys_argv('--brands=[]')
    def test_empty_explicit_list_single_str(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == []

    @mock_sys_argv('--brands', "['toyota', 'honda']")
    def test_explicit_list(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', 'honda']

    @mock_sys_argv("--brands=['toyota', 'honda']")
    def test_explicit_list_single_str(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', 'honda']

    @mock_sys_argv('--brands', 'toyota', 'null')
    def test_separate_args_include_none(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', None]

    @mock_sys_argv("--brands=['toyota', 'null']")
    def test_explicit_list_single_str_include_none(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', None]

    @mock_sys_argv('--brands', "['toyota', 'null']")
    def test_explicit_list_include_none(self):
        config = Config(default=LIST_CONTENTS)

        assert config.brands == ['toyota', None]


@contextlib.contextmanager
def tempfile(mode='w+b', buffering=-1, encoding=None,
             newline=None, suffix=None, prefix=None,
             dir=None):

    file = _tempfile.NamedTemporaryFile(mode=mode, buffering=buffering, encoding=encoding,
                                        newline=newline, suffix=suffix, prefix=prefix,
                                        dir=dir, delete=False)
    try:
        yield file
    finally:
        os.remove(file.name)
