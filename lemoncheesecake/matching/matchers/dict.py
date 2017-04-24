'''
Created on Apr 1, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import Matcher, match_failure, match_success, got
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "has_entry",
)

class HasEntry(Matcher):
    def __init__(self, key, value_matcher):
        self.key = key
        self.value_matcher = value_matcher
    
    def description(self):
        if self.value_matcher:
            return "has entry '%s' %s" % (self.key, self.value_matcher.description())
        else:
            return "has entry '%s'" % self.key
    
    def matches(self, actual):
        if self.key in actual:
            if self.value_matcher:
                return self.value_matcher.matches(actual[self.key])
            else:
                return match_success(got(actual[self.key]))
        else:
            return match_failure("No entry '%s'" % self.key)

def has_entry(key, value_matcher=None):
    """Test if dict has a <key> entry whose value matches (optional) value_matcher""" 
    return HasEntry(key, is_(value_matcher) if value_matcher != None else None)
