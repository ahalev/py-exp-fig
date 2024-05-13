import pytest

from expfig.core._parse import ListType
from expfig.core import str2none


class TestListTypeFromList:
    def test_all_str(self):
        list_like = 'a', 'b', 'c'
        list_type = ListType.from_list(list_like)

        assert list_type.type == str2none

    def test_all_int(self):
        list_like = 0, 4, 10
        list_type = ListType.from_list(list_like)

        assert list_type.type == int

    def test_all_float(self):
        list_like = 0.0, 4.5, 10.0
        list_type = ListType.from_list(list_like)

        assert list_type.type == float

    def test_nonunique(self):
        list_like = 'a', 0

        with pytest.warns(UserWarning, match='Collecting list-like argument'):
            list_type = ListType.from_list(list_like)

        assert list_type.type == str2none
