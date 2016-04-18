'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.testsuite import AbortTest

import sys
import re

def check(description, outcome, details=None):
    return get_runtime().check(description, outcome, details)

class Check:
    assertion = False
    description_prefix = "Verify that "
    description_fmt = None
    comparator = None
    always_details = False
    details_fmt = "Got {actual}"
    value_type = None
    
    def __init__(self, assertion=False):
        self.assertion = assertion
    
    def handle_assertion(self, outcome):
        if self.assertion and not outcome:
            raise AbortTest()
        return outcome
    
    def __call__(self, name, actual, expected):
        ret = self.compare(name, actual, expected)
        return self.handle_assertion(ret)
    
    def compare(self, name, actual, expected):
        outcome = self.comparator(actual, expected)
        description = self.description(name, expected)
        details = None
        if not outcome or self.always_details:
            details = self.details(actual)
        return check(description, outcome, details)
    
    def description(self, name, expected):
        description = self.description_prefix
        description += self.description_fmt.format(name=name, expected=expected)
        return description
    
    def details(self, actual):
        return self.details_fmt.format(actual=actual)

def check_and_assert(checker):
    return checker(), checker(assertion=True)

def do_register(name, checker_inst, assertion_inst):
    setattr(sys.modules[__name__], "check_%s" % name, checker_inst)
    setattr(sys.modules[__name__], "assert_%s" % name, assertion_inst)

def register_checker(name, checker, alias=None):
    checker_inst = checker()
    assertion_inst = checker(assertion=True)
    do_register(name, checker_inst, assertion_inst)
    if alias:
        do_register(alias, checker_inst, assertion_inst)

def alias_checker(alias, name):
    do_register(alias,
        getattr(sys.modules[__name__], "check_%s" % name),
        getattr(sys.modules[__name__], "assert_%s" % name)
    )

################################################################################
# Equality / non-equality checkers 
################################################################################

class CheckEq(Check):
    description_fmt = "'{name}' is equal to {expected}"
    comparator = staticmethod(lambda a, e: a == e)
register_checker("eq", CheckEq)

class CheckNotEq(Check):
    description_fmt = "'{name}' is not equal to {expected}"
    comparator = staticmethod(lambda a, e: a != e)
register_checker("not_eq", CheckNotEq)

################################################################################
# Greater than and Greater than or equal checkers 
################################################################################

class CheckGt(Check):
    description_fmt = "'{name}' is greater than {expected}"
    comparator = staticmethod(lambda a, e: a > e)
register_checker("gt", CheckGt)

class CheckGteq(Check):
    description_fmt = "'{name}' is greater or equal than {expected}"
    comparator = staticmethod(lambda a, e: a >= e)
register_checker("gteq", CheckGteq)

################################################################################
# Lower than and Lower than or equal checkers 
################################################################################

class CheckLt(Check):
    description_fmt = "'{name}' is lower than {expected}"
    comparator = staticmethod(lambda a, e: a < e)
register_checker("lt", CheckLt)

class CheckLteq(Check):
    description_fmt = "'{name}' is lower or equal than {expected}"
    comparator = staticmethod(lambda a, e: a <= e)
register_checker("lteq", CheckLteq)

################################################################################
# str checkers 
################################################################################

class CheckStrEq(CheckEq):
    description_fmt = "'{name}' is equal to '{expected}'"
register_checker("str_eq", CheckStrEq, alias="str")

class CheckStrNotEq(CheckNotEq):
    description_fmt = "'{name}' is not equal to '{expected}'"
register_checker("str_no_eq", CheckStrNotEq)

################################################################################
# list checkers 
################################################################################

alias_checker("list_eq", "eq")
alias_checker("list", "list_eq")

class CheckListLen(Check):
    description_fmt = "'{name}' list has {expected} elements"
    comparator = staticmethod(lambda a, e: len(a) == e)
    details = staticmethod(lambda a: "Got %d elements: %s" % (len(a), a))
register_checker("list_len_eq", CheckListLen, alias="list_len")

class CheckListContains(Check):
    description_fmt = "'{name}' list contains elements: {expected}"
    
    def compare(self, name, actual, expected):
        description = self.description(name, expected)
        
        missing = expected[:]
        for elem in missing:
            if elem in actual:
                missing.remove(elem)
        if missing:
            details = "Missing elements %s in list %s" % (missing, actual)
            return check(description, False, details)
        else:
            return check(description, True, None)
register_checker("list_contains", CheckListContains)

################################################################################
# dict checkers 
################################################################################

class CheckDictHasKey(Check):
    description_fmt = "'{name}' has entry '{expected}'"
    comparator = staticmethod(lambda a, e: a.has_key(e))
register_checker("dict_has_key", CheckDictHasKey)

class CheckDictValue(Check):
    def __call__(self, expected_key, actual, expected_value, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker(expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.description(expected_key, expected_value), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value", CheckDictValue)

class CheckDictValue2(Check):
    def __call__(self, expected_key, actual, expected, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker(expected_key, actual[expected_key], expected[expected_key])
        else:
            check(value_checker.description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value2", CheckDictValue2)

class CheckDictValue2WithDefault(Check):
    def __call__(self, expected_key, actual, expected, value_checker, default):
        if actual.has_key(expected_key):
            expected_value = expected.get(expected_key, default)
            ret = value_checker(expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value2_with_default", CheckDictValue2WithDefault)