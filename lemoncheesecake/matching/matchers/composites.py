'''
Created on Mar 28, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import Matcher, match_success, match_failure, match_result, \
    got_value, to_be, merge_match_result_descriptions

__all__ = (
    "all_of", "any_of", "anything", "something", "existing", "is_", "not_"
)

class AllOf(Matcher):
    def __init__(self, matchers):
        self.matchers = matchers
    
    def description(self, conjugate=False):
        return " and ".join([matcher.description(conjugate) for matcher in self.matchers])
    
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
        return " or ".join([matcher.description(conjugate) for matcher in self.matchers])
    
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
    def __init__(self, wording="anything"):
        self.wording = wording
    
    def description(self, conjugate=False):
        return "%s %s" % (to_be(conjugate), self.wording)
    
    def matches(self, actual):
        return match_success(got_value(actual))

def anything():
    """Matches anything (always success, whatever the actual value)"""
    return Anything()

def something():
    """Same thing as the 'anything' matcher but use 'something' in the matcher description"""
    return Anything(wording="something")

def existing():
    """Same thing as the 'anything' matcher but use 'existing' in the matcher description"""
    return Anything(wording="existing")

def is_(matcher):
    """If the function argument is not an instance of Matcher, wrap it into
    a matcher using equal_to, otherwise return the matcher argument as-is"""
    from lemoncheesecake.matching.matchers.value import equal_to
    return matcher if isinstance(matcher, Matcher) else equal_to(matcher)

class Not(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher
    
    def description(self, conjugate=False):
        return "not %s" % self.matcher.description(conjugate)
    
    def matches(self, actual):
        result = self.matcher.matches(actual)
        return match_result(not result.outcome, result.description)

def not_(matcher):
    """Negates the matcher in argument"""
    return Not(is_(matcher))