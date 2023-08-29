import pytest

from expfig.functions import unflatten, flatten

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2
}


class TestNest:
    def test_no_nest(self):
        restructured = unflatten(CONTENTS)

        assert restructured == CONTENTS

    def test_single_key(self):
        contents = {'jeep.car': 'vroom'}
        restructured = unflatten(contents)
        assert restructured == {'jeep': {'car': 'vroom'}}

    def test_two_toplevel_keys(self):
        contents = {
            'jeep.sound': 'vroom',
            'truck.sound': 'skirt'
        }
        expected = {
            'jeep': {'sound': 'vroom'},
            'truck': {'sound': 'skirt'}
        }

        restructured = unflatten(contents)
        assert restructured == expected

    def test_two_inner_keys(self):
        contents = {
            'jeep.sound': 'vroom',
            'jeep.wheels': 4
        }
        expected = {'jeep': {
            'sound': 'vroom',
            'wheels': 4
        }}

        restructured = unflatten(contents)
        assert restructured == expected

    def test_combination(self):
        contents = {
            'jeep.sound': 'vroom',
            'jeep.wheels': 4,
            'truck.sound': 'skirt',
            'truck.wheels': 18,
            'truck.axles.length': 32,
            'truck.axles.width': 4,
            'porsche': 'stunning'
        }
        expected = {
            'jeep': {'sound': 'vroom', 'wheels': 4},
            'truck': {'sound': 'skirt', 'wheels': 18, 'axles': {'length': 32, 'width': 4}},
            'porsche': 'stunning'
        }

        restructured = unflatten(contents)
        assert restructured == expected


class TestUnnest:
    def test_single_key(self):
        nested = {'jeep': {'car': 'vroom'}}
        unnested = flatten(nested)
        expected_contents = {'jeep.car': 'vroom'}
        assert unnested == expected_contents

    def test_single_key_namespacify(self):
        from expfig import Namespacify
        nested = Namespacify({'jeep': {'car': 'vroom'}})
        unnested = flatten(nested)
        expected_contents = {'jeep.car': 'vroom'}
        assert unnested == expected_contents

    def test_two_toplevel_keys(self):
        contents = {
            'jeep': {'sound': 'vroom'},
            'truck': {'sound': 'skirt'}
        }

        expected = {
            'jeep.sound': 'vroom',
            'truck.sound': 'skirt'
        }

        flat = flatten(contents)
        assert flat == expected

    def test_two_inner_keys(self):
        contents = {'jeep': {
            'sound': 'vroom',
            'wheels': 4
        }}

        expected = {
            'jeep.sound': 'vroom',
            'jeep.wheels': 4
        }

        flat = flatten(contents)
        assert flat == expected

    def test_combination(self):
        contents = {
            'jeep': {'sound': 'vroom', 'wheels': 4},
            'truck': {'sound': 'skirt', 'wheels': 18, 'axles': {'length': 32, 'width': 4}},
            'porsche': 'stunning'
        }

        expected = {
            'jeep.sound': 'vroom',
            'jeep.wheels': 4,
            'truck.sound': 'skirt',
            'truck.wheels': 18,
            'truck.axles.length': 32,
            'truck.axles.width': 4,
            'porsche': 'stunning'
        }

        flat = flatten(contents)
        assert flat == expected

    def test_combination_max_levels_2(self):
        contents = {
            'jeep': {'sound': 'vroom', 'wheels': 4},
            'truck': {'sound': 'skirt', 'wheels': 18, 'axles': {'length': 32, 'width': 4}},
            'porsche': 'stunning'
        }

        expected = {
            'jeep.sound': 'vroom',
            'jeep.wheels': 4,
            'truck.sound': 'skirt',
            'truck.wheels': 18,
            'truck.axles': {'length': 32, 'width': 4},
            'porsche': 'stunning'
        }

        flat = flatten(contents, levels=2)
        assert flat == expected

    def test_combination_max_levels_neg_1(self):
        contents = {
            'jeep': {'sound': 'vroom', 'wheels': 4},
            'truck': {'sound': 'skirt', 'wheels': 18, 'axles': {'length': 32, 'width': 4}},
            'porsche': 'stunning'
        }

        expected = {
            'jeep': {'sound': 'vroom', 'wheels': 4},
            'truck.sound': 'skirt',
            'truck.wheels': 18,
            'truck.axles': {'length': 32, 'width': 4},
            'porsche': 'stunning'
        }

        flat = flatten(contents, levels=-1)
        assert flat == expected
