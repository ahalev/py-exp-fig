import pytest
import pandas as pd
import yaml

from copy import deepcopy

from expfig.namespacify import Namespacify

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


class TestSimpleNamespacify:
    def test_empty(self):
        namespacify = Namespacify({})
        assert namespacify.name == ''
        assert len(namespacify) == 0
        assert namespacify.to_dict() == {}

    def test_nonempty_name(self):
        namespacify = Namespacify({}, name='name')
        assert namespacify.name == 'name'
        assert len(namespacify) == 0
        assert namespacify.to_dict() == {}

    def test_simple_contents(self):
        namespacify = Namespacify(CONTENTS)
        assert len(namespacify) == 3

        for key, value in CONTENTS.items():
            assert key in namespacify
            assert hasattr(namespacify, key)
            assert namespacify[key] == value

        assert namespacify.to_dict() == CONTENTS

    def test_with_name_from_keys(self):
        namespacify = Namespacify(CONTENTS).with_name_from_keys('car')

        assert namespacify.name == 'vroom'.upper()

    def test_with_name_from_keys_bad_key(self):
        namespacify = Namespacify(CONTENTS)
        with pytest.raises(KeyError):
            _ = namespacify.with_name_from_keys('jeep')

    def test_with_name_from_keys_too_many_keys(self):
        namespacify = Namespacify(CONTENTS)
        with pytest.raises(KeyError):
            _ = namespacify.with_name_from_keys('car', 'jeep')

    def test_name_key_raises_name_error(self):
        contents = CONTENTS.copy()
        contents['name'] = 'jeep'
        with pytest.raises(NameError):
            _ = Namespacify(contents)

    def test_serialize(self):
        namespacify = Namespacify(CONTENTS)
        dumped_and_loaded = yaml.safe_load(yaml.safe_dump(namespacify))
        loaded_namespacify = Namespacify(dumped_and_loaded)

        assert dumped_and_loaded == namespacify.to_dict()
        assert loaded_namespacify == namespacify
        assert loaded_namespacify is not namespacify

    def test_deserialize(self):
        namespacify = Namespacify(CONTENTS)
        dumped = yaml.safe_dump(namespacify)
        loaded_namespacify = Namespacify.deserialize(dumped)

        assert loaded_namespacify == namespacify
        assert loaded_namespacify is not Namespacify

    def test_update_existing_key(self):
        namespacify = Namespacify(CONTENTS)
        namespacify.update(car='zoom')

        assert len(namespacify) == 3

        for key, value in CONTENTS.items():
            assert key in namespacify
            assert hasattr(namespacify, key)
            if key == 'car':
                assert namespacify[key] == 'zoom'
            else:
                assert namespacify[key] == value

    def test_update_new_key(self):
        namespacify = Namespacify(CONTENTS)
        namespacify.update(sound='zoom')

        assert len(namespacify) == 4

        for key, value in CONTENTS.items():
            assert key in namespacify
            assert hasattr(namespacify, key)
            assert namespacify[key] == value

        assert 'sound' in namespacify
        assert hasattr(namespacify, 'sound')
        assert namespacify['sound'] == 'zoom'

    def test_update_new_and_existing(self):
        namespacify = Namespacify(CONTENTS)
        namespacify.update(car='zoom', sound='zoom-zoom')

        assert len(namespacify) == 4

        for key, value in CONTENTS.items():
            assert key in namespacify
            assert hasattr(namespacify, key)
            if key == 'car':
                assert namespacify[key] == 'zoom'
            else:
                assert namespacify[key] == value

        assert 'sound' in namespacify
        assert hasattr(namespacify, 'sound')
        assert namespacify['sound'] == 'zoom-zoom'


class TestNestNamespacify:
    def test_nested_contents(self):
        namespacify = Namespacify(NESTED_CONTENTS)
        assert len(namespacify) == 2

        for key, value in NESTED_CONTENTS.items():
            assert key in namespacify
            assert hasattr(namespacify, key)
            assert namespacify[key].to_dict() == value

            for inner_key, inner_val in value.items():
                assert hasattr(namespacify[key], inner_key)
                assert namespacify[key][inner_key] == inner_val

        assert namespacify.to_dict() == NESTED_CONTENTS

    def test_update(self):
        pass

    def test_exact_intersection(self):
        namespacify = Namespacify(NESTED_CONTENTS)
        print(deepcopy(namespacify))
        intersection = namespacify.intersection(namespacify)
        assert intersection == namespacify

    def test_intersection_top_level_difference(self):
        other_contents = deepcopy(NESTED_CONTENTS)
        other_contents['jeep'] = 'missing'

        ns1 = Namespacify(NESTED_CONTENTS)
        ns2 = Namespacify(other_contents)

        intersection1 = ns1.intersection(ns2)
        intersection2 = ns2.intersection(ns1)

        assert intersection1 == intersection2

        assert 'jeep' not in intersection1

        for k, v in NESTED_CONTENTS.items():
            if k == 'jeep':
                continue
            else:
                assert k in intersection1
                assert intersection1[k] == v

    def test_intersection_bottom_level_difference(self):
        other_contents = deepcopy(NESTED_CONTENTS)
        other_contents['jeep']['car'] = 'missing'

        ns1 = Namespacify(NESTED_CONTENTS)
        ns2 = Namespacify(other_contents)

        intersection1 = ns1.intersection(ns2)
        intersection2 = ns2.intersection(ns1)

        assert intersection1 == intersection2

        assert 'jeep' in intersection1
        assert 'car' not in intersection1['jeep']

        for k, v in NESTED_CONTENTS.items():
            if k == 'jeep':
                for k_i, v_i in v.items():
                    if k_i == 'car':
                        continue
                    assert v_i == intersection1[k][k_i]
            else:
                assert k in intersection1
                assert intersection1[k] == v

    def test_to_series(self):
        ns = Namespacify(NESTED_CONTENTS)
        series = ns.to_series()

        assert series.loc['jeep'].equals(pd.Series(CONTENTS))
        assert series.loc['truck'].equals(pd.Series(NESTED_CONTENTS['truck']))
        assert series.loc[pd.IndexSlice[:, 'car']].equals(pd.Series(['vroom', 'skirt'], index=['jeep', 'truck']))
