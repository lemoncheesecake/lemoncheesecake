'''
Created on Apr 1, 2017

@author: nicolas
'''

from lemoncheesecake.exceptions import method_not_implemented
from lemoncheesecake.matching.base import Matcher, match_failure, match_success, got_value, to_have
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "has_entry",
)

class EntryMatcher:
    def description(self):
        method_not_implemented("description", self)
    
    def get_entry(self, actual):
        """Return the value of dict corresponding to entry matching or raise KeyError if entry is not found""" 
        method_not_implemented("get_entry", self)

class KeyMatcher(EntryMatcher):
    def __init__(self, key):
        self.key = key
    
    def description(self):
        return '"%s"' % self.key
    
    def get_entry(self, actual):
        return actual[self.key]

def wrap_key_matcher(key_matcher):
    if isinstance(key_matcher, EntryMatcher):
        return key_matcher
    return KeyMatcher(key_matcher)

class HasEntry(Matcher):
    def __init__(self, key_matcher, value_matcher):
        self.key_matcher = key_matcher
        self.value_matcher = value_matcher
    
    def description(self, conjugate=False):
        ret = '%s entry %s' % (to_have(conjugate), self.key_matcher.description())
        if self.value_matcher:
            ret += " that " + self.value_matcher.description(conjugate=True)
        return ret
    
    def matches(self, actual):
        try:
            value = self.key_matcher.get_entry(actual)
        except KeyError:
            return match_failure('No entry "%s"' % self.key_matcher.description())
        
        if self.value_matcher:
            return self.value_matcher.matches(value)
        else:
            return match_success(got_value(value))

def has_entry(key_matcher, value_matcher=None):
    """Test if dict has a <key> entry whose value matches (optional) value_matcher""" 
    return HasEntry(wrap_key_matcher(key_matcher), is_(value_matcher) if value_matcher != None else None)
