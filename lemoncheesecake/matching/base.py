'''
Created on Mar 27, 2017

@author: nicolas
'''

import json

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
    def description(self, conjugate=False):
        method_not_implemented("description", self)
    
    def matches(self, actual):
        method_not_implemented("match", self)

class MatchExpected(Matcher):
    def __init__(self, expected):
        self.expected = expected

def serialize_value(value):
    return json.dumps(value, ensure_ascii=False)

def serialize_values(values):
    return ", ".join(map(serialize_value, values))

def got(value):
    return "Got %s" % value

def got_value(value):
    return got(serialize_value(value))

def got_values(values):
    return got(serialize_values(values))

def merge_match_result_descriptions(results):
    return ", ".join(
        get_distincts_in_list([result.description for result in results if result.description != None])
    )

def to_be(conjugate=False):
    return "is" if conjugate else "to be"

def to_have(conjugate=False):
    return "has" if conjugate else "to have"
