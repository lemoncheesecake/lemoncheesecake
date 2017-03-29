'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.utils import get_distincts_in_list
from lemoncheesecake.exceptions import method_not_implemented

class MatchResult:
    def __init__(self, outcome, description):
        self.outcome = outcome
        self.description = description
    
    def is_success(self):
        return self.outcome == True
    
    def is_failure(self):
        return self.outcome == False

def match_success(description=None):
    return MatchResult(True, description)

def match_failure(description):
    return MatchResult(False, description)

def match_result(outcome, description=None):
    return MatchResult(outcome, description)

class Matcher:
    def description(self):
        method_not_implemented("description", self)
    
    def matches(self, actual):
        method_not_implemented("match", self)

class MatchExpected(Matcher):
    def __init__(self, expected):
        self.expected = expected

def value_repr(value):
    return repr(value)

def got(value):
    return "Got %s" % value

def merge_match_result_descriptions(results):
    return ", ".join(
        get_distincts_in_list([result.description for result in results if result.description != None])
    )