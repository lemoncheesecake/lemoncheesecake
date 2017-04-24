'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import MatchExpected, Matcher, match_success, match_failure, got
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "equal_to", "not_equal_to", "greater_than", "greater_than_or_equal_to",
    "less_than", "less_than_or_equal_to", "is_none", "is_not_none", "has_length"
)

class Equal(MatchExpected):
    def description(self):
        return "is equal to %s"  % self.expected
    
    def matches(self, actual):
        if actual == self.expected:
            return match_success()
        else:
            return match_failure(got(actual))

def equal_to(expected):
    """Test if value is equal to expected"""
    return Equal(expected)

class NotEqual(MatchExpected):
    def description(self):
        return "is not equal to %s"  % self.expected
    
    def matches(self, actual):
        if actual != self.expected:
            return match_success(got(actual))
        else:
            return match_failure(got(actual))

def not_equal_to(expected):
    """Test if value is not equal to expected"""
    return NotEqual(expected)

class Greater(MatchExpected):
    def description(self):
        return "is greater than %s"  % self.expected
    
    def matches(self, actual):
        if actual > self.expected:
            return match_success(got(actual))
        else:
            return match_failure(got(actual))

def greater_than(expected):
    """Test if value is greater than expected"""
    return Greater(expected)

class GreaterThanOrEqualTo(MatchExpected):
    def description(self):
        return "is greater than or equal to %s"  % self.expected
    
    def matches(self, actual):
        if actual >= self.expected:
            return match_success(got(actual))
        else:
            return match_failure(got(actual))

def greater_than_or_equal_to(expected):
    """Test if value is greater or equal than expected"""
    return GreaterThanOrEqualTo(expected)

class LessThan(MatchExpected):
    def description(self):
        return "is less than %s" % self.expected
    
    def matches(self, actual):
        if actual < self.expected:
            return match_success(got(actual))
        else:
            return match_failure(got(actual))

def less_than(expected):
    """Test if value is less than expected"""
    return LessThan(expected)

class LessThanOrEqualTo(MatchExpected):
    def description(self):
        return "is less than or equal to %s"  % self.expected
    
    def matches(self, actual):
        if actual <= self.expected:
            return match_success(got(actual))
        else:
            return match_failure(got(actual))

def less_than_or_equal_to(expected):
    """Test if value is less than or equal to expected"""
    return LessThanOrEqualTo(expected)

def is_none():
    """Test if value is None"""
    return equal_to(None)

def is_not_none():
    """Test if value is not None"""
    return not_equal_to(None)

class HasLength(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher
    
    def description(self):
        return "whose length %s" % self.matcher.description()
    
    def matches(self, actual):
        return self.matcher.matches(len(actual))

def has_length(length):
    """Test if value has length"""
    return HasLength(is_(length))
