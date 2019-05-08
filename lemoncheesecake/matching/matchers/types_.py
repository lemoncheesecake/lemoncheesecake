'''
Created on Apr 3, 2017

@author: nicolas
'''

import six

from lemoncheesecake.matching.base import Matcher, match_success, match_failure, got, serialize_value, got_value, to_be
from lemoncheesecake.matching.matchers.value import is_

_TYPE_NAMES = {
    int: "integer",
    float: "float",
    str: "string",
    dict: "collection",
    list: "array", tuple: "array"
}
if six.PY2:
    _TYPE_NAMES[unicode] = "string",


class IsValueOfType(Matcher):
    def __init__(self, types, type_name, value_matcher):
        self.types = types
        self.type_name = type_name
        self.value_matcher = value_matcher

    def build_description(self, conjugate=False):
        ret = "%s %s" % (to_be(conjugate), self.type_name)
        if self.value_matcher:
            ret += " that %s" % self.value_matcher.description(conjugate=True)

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
                return match_success(got_value(actual))
        else:
            return match_failure(got("%s (%s)" % (serialize_value(actual), self._get_value_type_name(actual))))


def _is_type(types, type_name):
    def wrapper(value_matcher=None):
        return IsValueOfType(
            types, type_name, is_(value_matcher) if value_matcher is not None else None
        )
    wrapper.__doc__ = "Test if value is of type %s" % type_name
    return wrapper


is_integer = _is_type([int], "an integer")
is_float = _is_type([float], "a float")
is_bool = _is_type([bool], "a boolean")
is_str = _is_type([str] if six.PY3 else [str, unicode], "a string")
is_dict = _is_type([dict], "a collection")
is_list = _is_type([list, tuple], "a list")
