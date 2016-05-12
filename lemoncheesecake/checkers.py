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
    name = None
    assertion = False
    always_details = False
    comparator = None
    description_prefix = "Check that"
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
                return check(description, False, self.format_details(actual))
        outcome = self.comparator(actual, expected)
        details = None
        if not outcome or self.always_details:
            details = self.format_details(actual)
        return check(description, outcome, details)
    
    def format_actual_value(self, value):
        return "%s" % value
    format_expected_value = format_actual_value
    
    def format_description(self, name, expected):
        description = "{prefix} {name} {comparator} {expected}".format(
            prefix=self.description_prefix, name=name,
            comparator=self.comparator_label, expected=self.format_expected_value(expected)
        )
        if self.value_type:
            description += " (%s)" % self.value_type.__name__
        return description
    
    def format_details(self, actual):
        details = "Got %s" % self.format_actual_value(actual)
        if self.value_type:
            details += " (%s)" % type(actual).__name__
        return details

def check_and_assert(checker):
    return checker(), checker(assertion=True)

def do_register(name, checker_inst, assertion_inst):
    setattr(sys.modules[__name__], "check_%s" % name, checker_inst)
    setattr(sys.modules[__name__], "assert_%s" % name, assertion_inst)

def register_checker(checker_class, alias=None, value_type=None):
    global BASE_CHECKER_NAMES
    
    if not checker_class.name:
        raise Exception("Missing name for checker class %s" % checker_class)
    
    BASE_CHECKER_NAMES.append(checker_class.name)
    
    checker_inst = checker_class(value_type=value_type)
    assertion_inst = checker_class(assertion=True, value_type=value_type)
    do_register(checker_class.name, checker_inst, assertion_inst)
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
    name = "eq"
    comparator_label = "is equal to"
    comparator = staticmethod(lambda a, e: a == e)
register_checker(CheckEq)

class CheckNotEq(Check):
    name = "not_eq"
    comparator_label = "is not equal to"
    comparator = staticmethod(lambda a, e: a != e)
register_checker(CheckNotEq)

################################################################################
# Greater than and Greater than or equal checkers 
################################################################################

class CheckGt(Check):
    name = "gt"
    comparator_label = "is greater than"
    comparator = staticmethod(lambda a, e: a > e)
register_checker(CheckGt)

class CheckGteq(Check):
    name = "gteq"
    comparator_label = "is greater or equal than"
    comparator = staticmethod(lambda a, e: a >= e)
register_checker(CheckGteq)

################################################################################
# Lower than and Lower than or equal checkers 
################################################################################

class CheckLt(Check):
    name = "lt"
    comparator_label = "is lower than"
    comparator = staticmethod(lambda a, e: a < e)
register_checker(CheckLt)

class CheckLteq(Check):
    name = "lteq"
    comparator_label = "is lower or equal than"
    comparator = staticmethod(lambda a, e: a <= e)
register_checker(CheckLteq)

################################################################################
# str checkers 
################################################################################

class CheckStrEq(CheckEq):
    name = "str_eq"
    format_expected_value = format_actual_value = staticmethod(lambda s: "'%s'" % s)
register_checker(CheckStrEq, alias="str")

class CheckStrNotEq(CheckStrEq, CheckNotEq):
    name = "str_not_eq"
register_checker(CheckStrNotEq)

class CheckStrMatchPattern(CheckStrEq):
    name = "str_match_pattern"
    comparator_label = "match pattern"
    format_expected_value = staticmethod(lambda p: "'%s'" % p.pattern)
    comparator = staticmethod(lambda a, e: bool(e.match(a)))
register_checker(CheckStrMatchPattern, alias="pattern")

class CheckStrDoesNotMatchPattern(CheckStrMatchPattern):
    name = "str_does_not_match_pattern"
    comparator_label = "does not match pattern"
    comparator = staticmethod(lambda a, e: not bool(e.match(a)))
register_checker(CheckStrDoesNotMatchPattern)

################################################################################
# Numeric checkers
################################################################################

def generate_comparator_checkers_for_type(type_):
    checker_classes = CheckEq, CheckNotEq, CheckGt, CheckGteq, CheckLt, CheckLteq
    for klass in checker_classes:
        do_register("%s_%s" % (type_.__name__, klass.name), 
                    klass(value_type=type_), klass(value_type=type_, assertion=True))

generate_comparator_checkers_for_type(int)
generate_comparator_checkers_for_type(float)

################################################################################
# list checkers 
################################################################################

alias_checker("list_eq", "eq")
alias_checker("list", "list_eq")

class CheckListLen(Check):
    name = "list_len_eq"
    comparator = staticmethod(lambda a, e: len(a) == e)
    def format_description(self, name, expected):
        return "{prefix} {name} contains {expected} elements".format(
            prefix=self.description_prefix, name=name, expected=expected
        )
    def format_details(self, actual):
        return "Got %d elements: %s" % (len(actual), actual)
register_checker(CheckListLen, alias="list_len")

class CheckListContains(Check):
    name = "list_contains"
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
register_checker(CheckListContains)

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
    name = "dict_has_key"
    comparator = staticmethod(lambda a, e: a.has_key(e))
    def format_description(self, name, expected):
        return "{prefix} {name} has entry '{expected}'".format(
            prefix=self.description_prefix, name=name, expected=expected
        )
register_checker(CheckDictHasKey)

class CheckDictValue(Check):
    name = "dict_value"
    def __call__(self, expected_key, actual, expected_value, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.format_description(expected_key, expected_value), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker(CheckDictValue)
register_dict_checkers("dict_value_%s", CheckDictValue)

class CheckDictValue2(Check):
    name = "dict_value2"
    def __call__(self, expected_key, actual, expected, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected[expected_key])
        else:
            check(value_checker.format_description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker(CheckDictValue2)
register_dict_checkers("dict_value_%s2", CheckDictValue2)

class CheckDictValue2WithDefault(Check):
    name = "dict_value2_with_default"
    def __call__(self, expected_key, actual, expected, value_checker, default):
        if actual.has_key(expected_key):
            expected_value = expected.get(expected_key, default)
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.format_description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
register_checker(CheckDictValue2WithDefault)
register_dict_checkers("dict_value_%s2_with_default", CheckDictValue2WithDefault)