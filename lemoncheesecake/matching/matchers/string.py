'''
Created on Apr 4, 2017

@author: nicolas
'''

import re

from lemoncheesecake.matching.base import MatchExpected, match_result, got, value_repr

__all__ = (
    "starts_with", "ends_with", "match_pattern"
)

_REGEXP_TYPE = type(re.compile("dummy"))

class StartsWith(MatchExpected):
    def description(self):
        return "starts with '%s'" % self.expected
    
    def matches(self, actual):
        return match_result(actual.startswith(self.expected), got(value_repr(actual)))

def starts_with(s):
    """Test if string begins with given prefix"""
    return StartsWith(s)

class EndsWith(MatchExpected):
    def description(self):
        return "ends with '%s'" % self.expected
    
    def matches(self, actual):
        return match_result(actual.endswith(self.expected), got(value_repr(actual)))

def ends_with(s):
    """Test if string ends with given suffix"""
    return EndsWith(s)

class MatchPattern(MatchExpected):
    def description(self):
        return "matches pattern '%s'" % self.expected.pattern
    
    def matches(self, actual):
        return match_result(self.expected.match(actual) != None, got(value_repr(actual)))

def match_pattern(pattern):
    """Test if string matches given pattern"""
    return MatchPattern(pattern if type(pattern) == _REGEXP_TYPE else re.compile(pattern))
