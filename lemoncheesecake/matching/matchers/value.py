'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import MatchExpected, Matcher, match_result, got_value, serialize_value, to_be, to_have
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "equal_to", "not_equal_to", "greater_than", "greater_than_or_equal_to",
    "less_than", "less_than_or_equal_to", "is_none", "is_not_none", "has_length"
)

def _comparator(comparison_description, comparison_func):
    def wrapper(expected):
        class _Comparator(MatchExpected):
            def description(self, conjugate=False):
                return "%s %s %s" % (to_be(conjugate), comparison_description, serialize_value(self.expected))
             
            def matches(self, actual):
                return match_result(comparison_func(actual, self.expected), got_value(actual))
         
        return _Comparator(expected)
     
    wrapper.__doc__ = """Test if value is %s than expected""" % comparison_description
    return wrapper

equal_to = _comparator("equal to", lambda a, e: a == e)
not_equal_to = _comparator("not equal to", lambda a, e: a != e)

greater_than = _comparator("greater than", lambda a, e: a > e)
greater_than_or_equal_to = _comparator("greater than or equal to", lambda a, e: a >= e)

less_than = _comparator("less than", lambda a, e: a < e)
less_than_or_equal_to = _comparator("greater than or equal to", lambda a, e: a <= e)

def is_none():
    """Test if value is None"""
    return equal_to(None)

def is_not_none():
    """Test if value is not None"""
    return not_equal_to(None)

class HasLength(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher
    
    def description(self, conjugate=False):
        return "%s a length that %s" % (to_have(conjugate), self.matcher.description(conjugate=True))
    
    def matches(self, actual):
        return self.matcher.matches(len(actual))

def has_length(length):
    """Test if value has a length of"""
    return HasLength(is_(length))
