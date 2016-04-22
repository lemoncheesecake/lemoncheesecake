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
    always_details = False
    comparator = None
    description_prefix = "Verify that "
    comparator_label = None
    value_type = None
    
    def __init__(self, assertion=False, value_type=None):
        self.assertion = assertion
        self.value_type = value_type
    
    def handle_assertion(self, outcome):
        if self.assertion and not outcome:
            raise AbortTest()
        return outcome
    
    def __call__(self, name, actual, expected):
        ret = self.compare(name, actual, expected)
        return self.handle_assertion(ret)
    
    def compare(self, name, actual, expected):
        description = self.format_description(name, expected)
        if self.value_type:
            if type(actual) != self.value_type:
                return check(description, False, self.details(actual) + "()")
        outcome = self.comparator(actual, expected)
        details = None
        if not outcome or self.always_details:
            details = self.details(actual)
        return check(description, outcome, details)
    
    def format_value(self, value):
        return "%s" % value
    
    def format_description(self, name, expected):
        return "{prefix} {name} {comparator} {expected}".format(
            prefix=self.description_prefix, name=name,
            comparator=self.comparator_label, self.format_value(expected)
        )
    
    def format_details(self, actual):
        return "Got %s" % self.format(actual)

def check_and_assert(checker):
    return checker(), checker(assertion=True)

def do_register(name, checker_inst, assertion_inst):
    setattr(sys.modules[__name__], "check_%s" % name, checker_inst)
    setattr(sys.modules[__name__], "assert_%s" % name, assertion_inst)

def register_checker(name, checker, alias=None, value_type=None):
    checker_inst = checker(value_type=value_type)
    assertion_inst = checker(assertion=True, value_type=value_type)
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
    comparator_label = "is equal to"
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
    comparator_label = "is greater than"
    comparator = staticmethod(lambda a, e: a > e)
register_checker("gt", CheckGt)

class CheckGteq(Check):
    comparator_label = "is greater or equal than"
    comparator = staticmethod(lambda a, e: a >= e)
register_checker("gteq", CheckGteq)

################################################################################
# Lower than and Lower than or equal checkers 
################################################################################

class CheckLt(Check):
    comparator_label = "is lower than"
    comparator = staticmethod(lambda a, e: a < e)
register_checker("lt", CheckLt)

class CheckLteq(Check):
    comparator_label = "is lower or equal than"
    comparator = staticmethod(lambda a, e: a <= e)
register_checker("lteq", CheckLteq)

################################################################################
# str checkers 
################################################################################

class CheckStrEq(CheckEq):
    format_value = staticmethod(lambda s: "'%s'"% s)
register_checker("str_eq", CheckStrEq, alias="str")

class CheckStrNotEq(CheckStrEq, CheckNotEq):
    pass
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