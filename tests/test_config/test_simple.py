import sys
import pytest

from unittest import mock
from expfig import Config

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2
}


def mock_sys_argv(args):
    return mock.patch.object(sys, 'argv', args)


class TestSimpleConfig:

    def test_dashed_key_exception(self):
        default = {'car-brand': 'yoda', **CONTENTS}
        with pytest.raises(NameError, match="Invalid character '-' in key 'car-brand'"):
            _ = Config(default=default)
