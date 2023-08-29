import pytest

from expfig.functions import nest, unnest

CONTENTS = {
    'car': 'vroom',
    'wheels': 4,
    'axles': 2
}


class TestRestructure:
    def test_no_restructure(self):
        restructured = restructure_arguments(CONTENTS)

        assert restructured == CONTENTS

    def test_single_key(self):
        contents = {'jeep.car': 'vroom'}
        restructured = restructure_arguments(contents)
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

        restructured = restructure_arguments(contents)
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

        restructured = restructure_arguments(contents)
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

        restructured = restructure_arguments(contents)
        assert restructured == expected
