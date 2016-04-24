'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.testsuite import AbortTest

import sys
import re

BASE_CHECKER_NAMES = [ ]

def check(description, outcome, details=None):
    return get_runtime().check(description, outcome, details)

class Check:
    assertion = False
    always_details = False
    comparator = None
    description_prefix = "Verify that"
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
                return check(description, False, self.format_details(actual) + "()")
        outcome = self.comparator(actual, expected)
        details = None
        if not outcome or self.always_details:
            details = self.format_details(actual)
        return check(description, outcome, details)
    
    def format_value(self, value):
        return "%s" % value
    
    def format_description(self, name, expected):
        return "{prefix} {name} {comparator} {expected}".format(
            prefix=self.description_prefix, name=name,
            comparator=self.comparator_label, expected=self.format_value(expected)
        )
    
    def format_details(self, actual):
        return "Got %s" % self.format_value(actual)

def check_and_assert(checker):
    return checker(), checker(assertion=True)

def do_register(name, checker_inst, assertion_inst):
    setattr(sys.modules[__name__], "check_%s" % name, checker_inst)
    setattr(sys.modules[__name__], "assert_%s" % name, assertion_inst)

def register_checker(name, checker, alias=None, value_type=None):
    global BASE_CHECKER_NAMES
    BASE_CHECKER_NAMES.append(name)
    
    checker_inst = checker(value_type=value_type)
    assertion_inst = checker(assertion=True, value_type=value_type)
    do_register(name, checker_inst, assertion_inst)
    if alias:
        do_register(alias, checker_inst, assertion_inst)

def get_checker(name):
    return getattr(sys.modules[__name__], "check_%s" % name)

def get_assertion(name):
    return getattr(sys.modules[__name__], "assert_%s" % name)

def alias_checker(alias, name):
    do_register(alias, get_checker(name), get_assertion(name))

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
    comparator = staticmethod(lambda a, e: len(a) == e)
    def format_description(self, name, expected):
        return "{prefix} {name} contains {expected} elements".format(
            prefix=self.description_prefix, name=name, expected=expected
        )
    def format_details(self, actual):
        return "Got %d elements: %s" % (len(actual), actual)
register_checker("list_len_eq", CheckListLen, alias="list_len")

class CheckListContains(Check):
    comparator_label = "contains elements"
    
    def compare(self, name, actual, expected):
        description = self.format_description(name, expected)
        
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

def register_dict_checkers(dict_checker_name_fmt, dict_checker):
    def wrapper(value_checker):
        class dict_value_checker(dict_checker):
            def __call__(self, *args, **kwargs):
                kwargs["value_checker"] = value_checker
                return dict_checker.__call__(self, *args, **kwargs)
        return dict_value_checker
    global BASE_CHECKER_NAMES
    for name in BASE_CHECKER_NAMES:
        klass = wrapper(get_checker(name))
        do_register(dict_checker_name_fmt % name, klass(), klass(assertion=True))

class CheckDictHasKey(Check):
    comparator = staticmethod(lambda a, e: a.has_key(e))
    def format_description(self, name, expected):
        return "{prefix} {name} has entry '{expected}'".format(
            prefix=self.description_prefix, name=name, expected=expected
        )
register_checker("dict_has_key", CheckDictHasKey)

class CheckDictValue(Check):
    def __call__(self, expected_key, actual, expected_value, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.format_description(expected_key, expected_value), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value", CheckDictValue)
register_dict_checkers("dict_%s", CheckDictValue)

class CheckDictValue2(Check):
    def __call__(self, expected_key, actual, expected, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected[expected_key])
        else:
            check(value_checker.format_description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value2", CheckDictValue2)
register_dict_checkers("dict_%s2", CheckDictValue2)

class CheckDictValue2WithDefault(Check):
    def __call__(self, expected_key, actual, expected, value_checker, default):
        if actual.has_key(expected_key):
            expected_value = expected.get(expected_key, default)
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.format_description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker("dict_value2_with_default", CheckDictValue2WithDefault)
register_dict_checkers("dict_%s2_with_default", CheckDictValue2WithDefault)