import pytest

from expfig.core._parse import ListType, parse_arg_type
from expfig.core import str2none, str2bool, TypeToNone


class TestListTypeFromList:
    def test_all_str(self):
        list_like = 'a', 'b', 'c'
        list_type = ListType.from_list(list_like)

        assert list_type.type == str

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

        assert list_type.type == 'any'

    @pytest.mark.parametrize('value', ('a', 1, ['a', 1], ['a', 1, ['a', 1]]))
    def test_nonunique_parse(self, value):
        list_like = 'a', 0

        with pytest.warns(UserWarning, match='Collecting list-like argument'):
            list_type = ListType.from_list(list_like)

        parsed = list_type(str(value))

        assert parsed == value

    @pytest.mark.parametrize('value', ('a', 1, ['a', 1], ['a', 1, ['a', 1]]))
    def test_none_parse(self, value):
        list_type = ListType.from_list([None])
        parsed = list_type(str(value))

        assert parsed == value


class TestParseArgType:
    def test_str(self):
        parsed_type, _ = parse_arg_type('abc')
        assert parsed_type == str2none

    def test_bool(self):
        parsed_type, _ = parse_arg_type(True)
        assert parsed_type == str2bool

    def test_int(self):
        parsed_type, _ = parse_arg_type(1)
        assert parsed_type == TypeToNone(int)

    def test_float(self):
        parsed_type, _ = parse_arg_type(1.0)
        assert parsed_type == TypeToNone(float)

    def test_list_of_int(self):
        parsed_type, additional_args = parse_arg_type([1, 2, 3])
        assert parsed_type == ListType(TypeToNone(int))

    def test_list_of_str(self):
        parsed_type, additional_args = parse_arg_type(list('abcd'))
        assert parsed_type == ListType(str2none)
