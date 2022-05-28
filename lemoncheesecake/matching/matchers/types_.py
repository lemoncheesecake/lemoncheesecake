'''
Created on Apr 3, 2017

@author: nicolas
'''

from typing import List, Any, Union

from lemoncheesecake.helpers.text import jsonify
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer
from lemoncheesecake.matching.matchers.value import is_

_TYPE_NAMES = {
    int: "integer",
    float: "float",
    str: "string",
    dict: "collection",
    list: "array", tuple: "array"
}


class IsValueOfType(Matcher):
    def __init__(self, types: List[Any], type_name: str, value_matcher: Matcher) -> None:
        self.types = types
        self.type_name = type_name
        self.value_matcher = value_matcher

    def build_description(self, transformation):
        ret = transformation("to be %s" % self.type_name)
        if self.value_matcher:
            ret += " that %s" % self.value_matcher.build_description(MatcherDescriptionTransformer(conjugate=True))

        return ret

    @staticmethod
    def _get_value_type_name(value):
        try:
            return _TYPE_NAMES[type(value)]
        except KeyError:
            return str(type(value))

    def matches(self, actual):
        if type(actual) in self.types:
            if self.value_matcher:
                return self.value_matcher.matches(actual)
            else:
                return MatchResult.success("got %s" % jsonify(actual))
        else:
            return MatchResult.failure("got %s (%s)" % (jsonify(actual), self._get_value_type_name(actual)))


def _is_type(types, type_name, value_matcher):
    return IsValueOfType(
        types, type_name, is_(value_matcher) if value_matcher is not None else None
    )


def is_integer(expected: Union[int, Matcher] = None) -> Matcher:
    """
    Test if value is an integer.
    """
    return _is_type([int], "an integer", expected)


def is_float(expected: Union[float, Matcher] = None) -> Matcher:
    """
    Test if value is a float.
    """
    return _is_type([float], "a float", expected)


def is_bool(expected: Union[bool, Matcher] = None) -> Matcher:
    """
    Test if value is a boolean.
    """
    return _is_type([bool], "a boolean", expected)


def is_str(expected: Union[str, Matcher] = None) -> Matcher:
    """
    Test if value is a string.
    """
    return _is_type([str], "a string", expected)


def is_dict(expected: Union[dict, Matcher] = None) -> Matcher:
    """
    Test if value is a dict (key/value collection).
    """
    return _is_type([dict], "a collection", expected)


def is_list(expected: Union[list, tuple, Matcher] = None) -> Matcher:
    """
    Test if value is a list.
    """
    return _is_type([list, tuple], "a list", expected)
