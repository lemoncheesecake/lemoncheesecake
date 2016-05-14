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
    always_display_details = False
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
        if not outcome or self.always_display_details:
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

def register_checker(name, checker_class, alias=None, value_type=None):
    global BASE_CHECKER_NAMES
    
    BASE_CHECKER_NAMES.append(name)
    
    checker_class.name = name
    checker_inst = checker_class(value_type=value_type)
    assertion_inst = checker_class(assertion=True, value_type=value_type)
    do_register(name, checker_inst, assertion_inst)
    if alias:
        do_register(alias, checker_inst, assertion_inst)

def checker(name, alias=None, value_type=None):
    def wrapper(klass):
        register_checker(name, klass, alias, value_type)
        return klass
    return wrapper

def get_checker(name):
    return getattr(sys.modules[__name__], "check_%s" % name)

def get_assertion(name):
    return getattr(sys.modules[__name__], "assert_%s" % name)

def alias_checker(alias, name):
    do_register(alias, get_checker(name), get_assertion(name))

################################################################################
# Equality / non-equality checkers 
################################################################################

@checker("eq")
class CheckEq(Check):
    comparator_label = "is equal to"
    comparator = staticmethod(lambda a, e: a == e)

@checker("not_eq")
class CheckNotEq(Check):
    comparator_label = "is not equal to"
    comparator = staticmethod(lambda a, e: a != e)
    always_display_details = True

################################################################################
# Greater than and Greater than or equal checkers 
################################################################################

@checker("gt")
class CheckGt(Check):
    comparator_label = "is greater than"
    comparator = staticmethod(lambda a, e: a > e)

@checker("gteq")
class CheckGteq(Check):
    comparator_label = "is greater or equal than"
    comparator = staticmethod(lambda a, e: a >= e)

################################################################################
# Lower than and Lower than or equal checkers 
################################################################################

@checker("lt")
class CheckLt(Check):
    comparator_label = "is lower than"
    comparator = staticmethod(lambda a, e: a < e)
    always_display_details = True

@checker("lteq")
class CheckLteq(Check):
    comparator_label = "is lower or equal than"
    comparator = staticmethod(lambda a, e: a <= e)
    always_display_details = True

################################################################################
# str checkers 
################################################################################

@checker("str_eq", alias="str")
class CheckStrEq(CheckEq):
    name = "str_eq"
    format_expected_value = format_actual_value = staticmethod(lambda s: "'%s'" % s)

@checker("str_not_eq")
class CheckStrNotEq(CheckStrEq, CheckNotEq):
    always_display_details = True

@checker("str_match_pattern", alias="pattern")
class CheckStrMatchPattern(CheckStrEq):
    name = "str_match_pattern"
    comparator_label = "match pattern"
    format_expected_value = staticmethod(lambda p: "'%s'" % p.pattern)
    comparator = staticmethod(lambda a, e: bool(e.match(a)))
    always_display_details = True

@checker("str_does_not_match_pattern")
class CheckStrDoesNotMatchPattern(CheckStrMatchPattern):
    comparator_label = "does not match pattern"
    comparator = staticmethod(lambda a, e: not bool(e.match(a)))

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

@checker("list_len_eq", alias="list_len")
class CheckListLen(Check):
    comparator = staticmethod(lambda a, e: len(a) == e)
    def format_description(self, name, expected):
        return "{prefix} {name} contains {expected} elements".format(
            prefix=self.description_prefix, name=name, expected=expected
        )
    def format_details(self, actual):
        return "Got %d elements: %s" % (len(actual), actual)

@checker("list_contains")
class CheckListContains(Check):
    comparator_label = "contains elements"
    always_display_details = True
    
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

@checker("dict_has_key")
class CheckDictHasKey(Check):
    comparator = staticmethod(lambda a, e: a.has_key(e))
    def format_description(self, name, expected):
        return "{prefix} {name} has entry '{expected}'".format(
            prefix=self.description_prefix, name=name, expected=expected
        )

@checker("dict_value")
class CheckDictValue(Check):
    def __call__(self, expected_key, actual, expected_value, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.format_description(expected_key, expected_value), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)

register_dict_checkers("dict_value_%s", CheckDictValue)

@checker("dict_value2")
class CheckDictValue2(Check):
    def __call__(self, expected_key, actual, expected, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker("'%s'" % expected_key, actual[expected_key], expected[expected_key])
        else:
            check(value_checker.format_description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)

register_dict_checkers("dict_value_%s2", CheckDictValue2)

@checker("dict_value2_with_default")
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

register_dict_checkers("dict_value_%s2_with_default", CheckDictValue2WithDefault)