'''
Created on Apr 3, 2017

@author: nicolas
'''

from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.matching.base import Matcher, match_success, match_failure, got, value_repr
from lemoncheesecake.matching.matchers.value import is_

__all__ = (
    "is_integer", "is_float", "is_str", "is_dict", "is_list"
)

class IsValueOfType(Matcher):
    def __init__(self, types, type_name, value_matcher):
        self.types = types
        self.type_name = type_name
        self.value_matcher = value_matcher
    
    def description(self):
        if self.value_matcher:
            return "is %s and %s" % (self.type_name, self.value_matcher.description())
        else:
            return "is %s" % self.type_name
    
    def matches(self, actual):
        if type(actual) in self.types:
            if self.value_matcher:
                return self.value_matcher.matches(actual)
            else:
                return match_success(got(value_repr(actual)))
        else:
            return match_failure(got("%s (%s)" % (value_repr(actual), type(actual).__name__)))

def is_type(types, type_name):
    def wrapper(value_matcher=None):
        return IsValueOfType(
            types, type_name, is_(value_matcher) if value_matcher != None else None
        )
    return wrapper

is_integer = is_type([int], "integer")
is_float = is_type([float], "float")
is_str = is_type([str], "string") if IS_PYTHON3 else is_type([str, unicode], "string")
is_dict = is_type([dict], "collection")
is_list = is_type([list, tuple], "array")
