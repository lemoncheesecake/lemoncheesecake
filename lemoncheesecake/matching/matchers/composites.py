'''
Created on Mar 28, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import Matcher, match_success, match_failure, match_result, \
    got_value, to_be, merge_match_result_descriptions

__all__ = (
    "all_of", "any_of", "anything", "is_", "is_not"
)

class AllOf(Matcher):
    def __init__(self, matchers):
        self.matchers = matchers
    
    def description(self, conjugate=False):
        return " and ".join([matcher.description() for matcher in self.matchers])
    
    def matches(self, actual):
        results = []
        for matcher in self.matchers:
            result = matcher.matches(actual)
            if result.is_failure():
                return result
            results.append(result)
        
        return match_success(merge_match_result_descriptions(results))

def all_of(*matchers):
    """Test if all matchers match (logical AND between matchers)."""
    return AllOf(map(is_, matchers))

class AnyOf(Matcher):
    def __init__(self, matchers):
        self.matchers = matchers
    
    def description(self, conjugate=False):
        return " or ".join([matcher.description() for matcher in self.matchers])
    
    def matches(self, actual):
        results = []
        for matcher in self.matchers:
            match = matcher.matches(actual)
            if match.is_success():
                return match
            results.append(match)
        
        return match_failure(merge_match_result_descriptions(results))

def any_of(*matchers):
    """Test if at least one of the matcher match (logical OR between matchers)"""
    return AnyOf(map(is_, matchers))

class Anything(Matcher):
    def description(self, conjugate=False):
        return "%s anything" % to_be(conjugate)
    
    def matches(self, actual):
        return match_success(got_value(actual))

def anything():
    return Anything()

def is_(matcher):
    """If the function argument is not an instance of Matcher, wrap it into
    a matcher using equal_to, otherwise return the matcher argument as-is"""
    from lemoncheesecake.matching.matchers.value import equal_to
    return matcher if isinstance(matcher, Matcher) else equal_to(matcher)

class IsNot(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher
    
    def description(self, conjugate=False):
        return "not %s" % self.matcher.description(conjugate)
    
    def matches(self, actual):
        result = self.matcher.matches(actual)
        return match_result(not result.outcome, result.description)

def is_not(matcher):
    """Negates the matcher in argument"""
    return IsNot(is_(matcher))