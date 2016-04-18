'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.testsuite import AbortTest

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

################################################################################
# Equality / non-equality checkers 
################################################################################

class CheckEq(Check):
    description_fmt = "'{name}' is equal to {expected}"
    comparator = staticmethod(lambda a, e: a == e)
check_eq, assert_eq = check_and_assert(CheckEq)

class CheckNotEq(Check):
    description_fmt = "'{name}' is not equal to {expected}"
    comparator = staticmethod(lambda a, e: a != e)
check_not_eq, assert_not_eq = check_and_assert(CheckNotEq)

################################################################################
# Greater than and Greater than or equal checkers 
################################################################################

class CheckGt(Check):
    description_fmt = "'{name}' is greater than {expected}"
    comparator = staticmethod(lambda a, e: a > e)
check_gt, assert_gt = check_and_assert(CheckGt)

class CheckGteq(Check):
    description_fmt = "'{name}' is greater or equal than {expected}"
    comparator = staticmethod(lambda a, e: a >= e)
check_gteq, assert_gteq = check_and_assert(CheckGteq)

################################################################################
# Lower than and Lower than or equal checkers 
################################################################################

class CheckLt(Check):
    description_fmt = "'{name}' is lower than {expected}"
    comparator = staticmethod(lambda a, e: a < e)
check_lt, assert_lt = check_and_assert(CheckLt)

class CheckLteq(Check):
    description_fmt = "'{name}' is lower or equal than {expected}"
    comparator = staticmethod(lambda a, e: a <= e)
check_lteq, assert_lteq = check_and_assert(CheckLteq)

################################################################################
# str checkers 
################################################################################

class CheckStrEq(CheckEq):
    description_fmt = "'{name}' is equal to '{expected}'"
check_str_eq, assert_str_eq = check_and_assert(CheckStrEq)
check_str, assert_str = check_str_eq, assert_str_eq

class CheckStrNotEq(CheckNotEq):
    description_fmt = "'{name}' is not equal to '{expected}'"
check_str_not_eq, assert_str_not_eq = check_and_assert(CheckStrNotEq)

################################################################################
# list checkers 
################################################################################

class CheckListLen(Check):
    description_fmt = "'{name}' list has {expected} elements"
    comparator = staticmethod(lambda a, e: len(a) == e)
    details = staticmethod(lambda a: "Got %d elements: %s" % (len(a), a))
check_list_len_eq, assert_list_len_eq = check_and_assert(CheckListLen)
check_list_len, assert_list_len = check_list_len_eq, assert_list_len_eq

check_list_eq, assert_list_eq = check_eq, assert_eq
check_list, assert_list = check_list_eq, assert_list_eq

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
check_list_contains, assert_list_contains = check_and_assert(CheckListContains)

################################################################################
# dict checkers 
################################################################################

class CheckDictHasKey(Check):
    description_fmt = "'{name}' has entry '{expected}'"
    comparator = staticmethod(lambda a, e: a.has_key(e))
check_dict_has_key, assert_dict_has_key = check_and_assert(CheckDictHasKey)

class CheckDictValue(Check):
    def __call__(self, expected_key, actual, expected_value, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker(expected_key, actual[expected_key], expected_value)
        else:
            check(value_checker.description(expected_key, expected_value), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
check_dict_value, assert_dict_value = check_and_assert(CheckDictValue)

class CheckDictValue2(Check):
    def __call__(self, expected_key, actual, expected, value_checker):
        if actual.has_key(expected_key):
            ret = value_checker(expected_key, actual[expected_key], expected[expected_key])
        else:
            check(value_checker.description(expected_key, expected[expected_key]), False,
                  "There is no key '%s'" % expected_key)
            ret = False
        return self.handle_assertion(ret)
check_dict_value2, assert_dict_value2 = check_and_assert(CheckDictValue2)

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
check_dict_value2_with_default, assert_dict_value2_with_default = check_and_assert(CheckDictValue2WithDefault)
