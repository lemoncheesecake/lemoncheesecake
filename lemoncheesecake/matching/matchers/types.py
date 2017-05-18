'''
Created on Apr 3, 2017

@author: nicolas
'''

from lemoncheesecake.utils import IS_PYTHON3, IS_PYTHON2
from lemoncheesecake.matching.base import Matcher, match_success, match_failure, got, serialize_value, got_value, to_be
from lemoncheesecake.matching.matchers.value import is_

__all__ = (
    "is_integer", "is_float", "is_bool", "is_str", "is_dict", "is_list"
)

TYPE_NAMES = {
    int: "integer",
    float: "float",
    str: "string",
    dict: "collection",
    list: "array", tuple: "array"
}

if IS_PYTHON2:
    TYPE_NAMES[unicode] = "string",

def get_value_type_name(value):
    try:
        return TYPE_NAMES[type(value)]
    except KeyError:
        return str(type(value))

class IsValueOfType(Matcher):
    def __init__(self, types, type_name, value_matcher):
        self.types = types
        self.type_name = type_name
        self.value_matcher = value_matcher
    
    def description(self, conjugate=False):
        ret = "%s %s" % (to_be(conjugate), self.type_name)
        if self.value_matcher:
            ret += " that %s" % self.value_matcher.description(conjugate=True)
        
        return ret
    
    def matches(self, actual):
        if type(actual) in self.types:
            if self.value_matcher:
                return self.value_matcher.matches(actual)
            else:
                return match_success(got_value(actual))
        else:
            return match_failure(got("%s (%s)" % (serialize_value(actual), get_value_type_name(actual))))

def is_type(types, type_name):
    def wrapper(value_matcher=None):
        return IsValueOfType(
            types, type_name, is_(value_matcher) if value_matcher != None else None
        )
    wrapper.__doc__ = "Test if value is of type %s" % type_name
    return wrapper

is_integer = is_type([int], "an integer")
is_float = is_type([float], "a float")
is_bool = is_type([bool], "a boolean")
is_str = is_type([str] if IS_PYTHON3 else [str, unicode], "a string")
is_dict = is_type([dict], "a collection")
is_list = is_type([list, tuple], "a list")
