import pytest
import yaml

from copy import deepcopy
from types import ModuleType

from expfig.namespacify import Namespacify
from expfig.utils.get_pandas import pandas as pd

np = pytest.importorskip('numpy')

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
        assert len(namespacify) == 0
        assert namespacify.to_dict() == {}

    def test_nonempty_name(self):
        namespacify = Namespacify({})
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

    def test_name_key(self):
        # Holdover from when 'name' was not allowed as a key
        contents = CONTENTS.copy()
        contents['name'] = 'jeep'
        namespacify = Namespacify(contents)
        assert namespacify['name'] == 'jeep'

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

    @pytest.mark.skipif(not isinstance(pd, ModuleType), reason='pandas is not installed')
    def test_to_series(self):
        ns = Namespacify(NESTED_CONTENTS)
        series = ns.to_series()

        assert series.loc['jeep'].equals(pd.Series(CONTENTS))
        assert series.loc['truck'].equals(pd.Series(NESTED_CONTENTS['truck']))
        assert series.loc[pd.IndexSlice[:, 'car']].equals(pd.Series(['vroom', 'skirt'], index=['jeep', 'truck']))

    @pytest.mark.skipif(not isinstance(pd, ModuleType), reason='pandas is not installed')
    def test_to_series_empty(self):
        ns = Namespacify(dict())
        assert ns.to_series().empty

    def test_setitem_tuple(self):
        ns = Namespacify(NESTED_CONTENTS)
        ns[('truck', 'axles')] = 32

        assert ns['truck']['axles'] == 32
        assert isinstance(ns['truck'], Namespacify)

    def test_setitem_missing(self):
        ns = Namespacify(NESTED_CONTENTS)
        ns['bike'] = {'brand': 'honda', 'wheels': 2}

        assert ns['bike']['brand'] == 'honda'
        assert ns['bike']['wheels'] == 2

        assert isinstance(ns['bike'], Namespacify)

    def test_setitem_missing_tuple(self):
        ns = Namespacify(NESTED_CONTENTS)
        ns[('bike', 'brand')] = 'honda'
        ns[('bike', 'wheels')] = 2

        assert ns['bike']['brand'] == 'honda'
        assert ns['bike']['wheels'] == 2

        assert isinstance(ns['bike'], Namespacify)


class TestSymmetricDifference:
    def test_empty(self):
        ns1 = Namespacify(CONTENTS)
        ns2 = Namespacify(CONTENTS)

        sym_diff = ns1.symmetric_difference(ns2)
        assert len(sym_diff) == 0

    def test_simple(self):
        pass

    @pytest.mark.skipif(not isinstance(pd, ModuleType), reason='pandas is not installed')
    def test_arr_like(self):
        ns1 = Namespacify(CONTENTS)
        ns2 = Namespacify(CONTENTS)

        ns1['car'] = pd.Series(CONTENTS)

        sym_diff = ns1.symmetric_difference(ns2)

        assert np.array_equal(sym_diff['car'], ns1['car'])
