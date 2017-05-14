'''
Created on Apr 4, 2017

@author: nicolas
'''

import re

from lemoncheesecake.matching.base import MatchExpected, match_result, got_value

__all__ = (
    "starts_with", "ends_with", "contains_string", "match_pattern"
)

_REGEXP_TYPE = type(re.compile("dummy"))

class StartsWith(MatchExpected):
    def description(self, conjugate=False):
        return '%s with "%s"' % ("starts" if conjugate else "to start", self.expected)
    
    def matches(self, actual):
        return match_result(actual.startswith(self.expected), got_value(actual))

def starts_with(s):
    """Test if string begins with given prefix"""
    return StartsWith(s)

class EndsWith(MatchExpected):
    def description(self, conjugate=False):
        return '%s with "%s"' % ("ends" if conjugate else "to end", self.expected)
    
    def matches(self, actual):
        return match_result(actual.endswith(self.expected), got_value(actual))

def ends_with(s):
    """Test if string ends with given suffix"""
    return EndsWith(s)

class ContainsString(MatchExpected):
    def description(self, conjugate):
        return '%s with "%s"' % ("contains" if conjugate else "to contain", self.expected)
    
    def matches(self, actual):
        return match_result(self.expected in actual, got_value(actual))

def contains_string(s):
    """Test if string contains sub string"""
    return ContainsString(s)

class MatchPattern(MatchExpected):
    def description(self, conjugate=False):
        return '%s "%s"' % ("matches pattern" if conjugate else "to match pattern", self.expected.pattern)
    
    def matches(self, actual):
        return match_result(self.expected.match(actual) != None, got_value(actual))

def match_pattern(pattern):
    """Test if string matches given pattern"""
    return MatchPattern(pattern if type(pattern) == _REGEXP_TYPE else re.compile(pattern))
