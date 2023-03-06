import pytest
import yaml

from copy import deepcopy

from expfig import nested_dict_update

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2
}

NESTED_CONTENTS = {
    'jeep': CONTENTS,
    'truck': {
        'car': 'skirt',
        'wheels': 18,
        'axles': 6
    }
}

DOUBLE_NESTED_CONTENTS = {
    'american': NESTED_CONTENTS,
    'japanese': {'toyota': CONTENTS}
}


class TesteNestedDictUpdate:
    def test_empty(self):
        d = {}
        other = {}
        updated = nested_dict_update(d, other)
        assert updated is d
        assert len(updated) == 0

    def test_toplevel_update(self):
        d = deepcopy(CONTENTS)
        other = {'car': 'skirt'}

        updated = nested_dict_update(d, other)
        assert d is updated
        assert d['car'] == 'skirt'

    def test_lowlevel_update(self):
        d = deepcopy(NESTED_CONTENTS)
        other = {'truck': {'car': 'vroom'}}
        updated = nested_dict_update(d, other)

        assert d is updated
        assert d['truck']['car'] == 'vroom'

        assert d['jeep'] == CONTENTS
        assert d['truck']['wheels'] == NESTED_CONTENTS['truck']['wheels']
        assert d['truck']['axles'] == NESTED_CONTENTS['truck']['axles']

    def test_double_nested_dict_update(self):
        d = deepcopy(DOUBLE_NESTED_CONTENTS)
        other = {'american': {'jeep': {'car': 'vroom'}}}
        updated = nested_dict_update(d, other)
        assert d is updated

        assert d['japanese']['toyota'] == CONTENTS
        assert d['american']['jeep']['car'] == 'vroom'
        assert d['american']['jeep']['wheels'] == 4
        assert d['american']['jeep']['axles'] == 2
