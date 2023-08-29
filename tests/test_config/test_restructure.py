import pytest

from expfig.functions import nest, unnest

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2
}


class TestNest:
    def test_no_nest(self):
        restructured = nest(CONTENTS)

        assert restructured == CONTENTS

    def test_single_key(self):
        contents = {'jeep.car': 'vroom'}
        restructured = nest(contents)
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

        restructured = nest(contents)
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

        restructured = nest(contents)
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

        restructured = nest(contents)
        assert restructured == expected


class TestUnnest:
    def test_single_key(self):
        nested = {'jeep': {'car': 'vroom'}}
        unnested = unnest(nested)
        expected_contents = {'jeep.car': 'vroom'}
        assert unnested == expected_contents

    def test_single_key_namespacify(self):
        from expfig import Namespacify
        nested = Namespacify({'jeep': {'car': 'vroom'}})
        unnested = unnest(nested)
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

        flat = unnest(contents)
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

        flat = unnest(contents)
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

        flat = unnest(contents)
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

        flat = unnest(contents, levels=2)
        assert flat == expected
