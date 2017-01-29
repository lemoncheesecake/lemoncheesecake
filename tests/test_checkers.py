'''
Created on Dec 1, 2016

@author: nicolas
'''

import sys
import re
from types import FunctionType

import lemoncheesecake as lcc

from helpers import reporting_session, run_func_in_test

###
# check_eq
###

def test_check_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_eq("param", "foo", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "foo" in description
    assert outcome == True
    assert details == None

def test_check_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_eq("param", "bar", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "foo" in description
    assert outcome == False
    assert "bar" in details

###
# check_not_eq
###

def test_check_not_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_not_eq("param", "bar", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "foo" in description
    assert outcome == True
    assert "bar" in details

def test_check_not_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_not_eq("param", "foo", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "foo" in description
    assert outcome == False
    assert "foo" in details

###
# check_gt & check_gteq
###

def test_check_gt_success(reporting_session):
    run_func_in_test(lambda: lcc.check_gt("param", 42, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == True
    assert "42" in details

def test_check_gt_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_gt("param", 21, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == False
    assert "21" in details

def test_check_gteq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_gteq("param", 21, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == True
    assert "21" in details

def test_check_gteq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_gteq("param", 20, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == False
    assert "20" in details

###
# check_lt & check_lteq
###

def test_check_lt_success(reporting_session):
    run_func_in_test(lambda: lcc.check_lt("param", 21, 42))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == True
    assert "21" in details

def test_check_lt_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_lt("param", 21, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == False
    assert "21" in details

def test_check_lteq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_lteq("param", 21, 21))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == True
    assert "21" in details

def test_check_lteq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_lteq("param", 21, 20))
    description, outcome, details = reporting_session.get_last_check()
    
    assert outcome == False
    assert "21" in details

###
# check_str_eq & check_str_not_eq
###

def test_check_str_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_eq("param", "foo", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'foo'" in description
    assert outcome == True
    assert details == None

def test_check_str_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_eq("param", "bar", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'foo'" in description
    assert outcome == False
    assert "'bar'" in details

def test_check_str_not_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_not_eq("param", "bar", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'foo'" in description
    assert outcome == True
    assert "'bar'" in details

def test_check_str_not_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_not_eq("param", "foo", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'foo'" in description
    assert outcome == False
    assert "'foo'" in details

###
# check_str_match & check_str_does_not_match
###

def test_check_str_match_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_match("param", "foo", re.compile("^f")))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'^f'" in description
    assert outcome == True
    assert "'foo'" in details

def test_check_str_match_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_match("param", "bar", re.compile("^f")))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'^f'" in description
    assert outcome == False
    assert "'bar'" in details

def test_check_str_does_not_match_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_does_not_match("param", "bar", re.compile("^f")))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'^f'" in description
    assert outcome == True
    assert "'bar'" in details

def test_check_str_does_not_match_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_does_not_match("param", "foo", re.compile("^f")))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'^f'" in description
    assert outcome == False
    assert "'foo'" in details

###
# check_str_contains & check_str_does_not_contain
###

def test_check_str_contains_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_contains("param", "foobar", "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'bar'" in description
    assert outcome == True
    assert "'foobar'" in details

def test_check_str_contains_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_contains("param", "foobaz", "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'bar'" in description
    assert outcome == False
    assert "'foobaz'" in details

def test_check_str_does_not_contain_success(reporting_session):
    run_func_in_test(lambda: lcc.check_str_does_not_contain("param", "foobaz", "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'bar'" in description
    assert outcome == True
    assert "'foobaz'" in details

def test_check_str_does_not_contains_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_str_does_not_contain("param", "foobar", "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "'bar'" in description
    assert outcome == False
    assert "'foobar'" in details

###
# Typed checkers
###

def test_check_int_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_int_eq("param", 1, 1))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "int" in description and "1" in description
    assert outcome == True
    assert details == None

def test_check_int_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_int_eq("param", 1.0, 1))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "int" in description and "1" in description
    assert outcome == False
    assert "float" in details and "1.0" in details

def test_check_float_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_float_eq("param", 1.0, 1.0))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "float" in description and "1.0" in description
    assert outcome == True
    assert details == None

def test_check_float_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_float_eq("param", 1, 1.0))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "float" in description and "1.0" in description
    assert outcome == False
    assert "int" in details and "1" in details

def test_check_bool_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_bool_eq("param", False, False))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "bool" in description and "False" in description
    assert outcome == True
    assert details == None

def test_check_bool_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_bool_eq("param", 0, False))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "bool" in description and "False" in description
    assert outcome == False
    assert "int" in details and "0" in details

def test_check_typed_eq_none_success(reporting_session):
    run_func_in_test(lambda: lcc.check_int_eq("param", None, None))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "int" not in description and "None" in description
    assert outcome == True
    assert details == None

def test_check_typed_eq_none_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_int_eq("param", 42, None))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "int" not in description and "None" in description
    assert outcome == False
    assert "42" in details and "int" in details

###
# list checkers
###

def test_check_list_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_list_len("param", (1, 2, 3), 3))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "3" in description
    assert outcome == True
    assert details == None

def test_check_list_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_list_len("param", (1, 2), 3))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "3" in description
    assert outcome == False
    assert "(1, 2)" in details

def test_check_list_contains_success(reporting_session):
    run_func_in_test(lambda: lcc.check_list_contains("param", ("foo", "bar"), ("bar", )))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "bar" in description
    assert outcome == True
    assert details == None

def test_check_list_contains_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_list_contains("param", ("foo", "baz"), ("bar", )))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "bar" in description
    assert outcome == False
    assert details != None

###
# dict checkers
# TODO: key_label and show_actual arguments are not yet tested
###

def test_check_dict_has_key_success(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_key("foo", {"foo": 42}, "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert outcome == True
    assert details == None

def test_check_dict_has_key_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_key("foo", {"bar": 42}, "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert outcome == False
    assert details == None

def test_check_dict_has_not_key_success(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_not_key("foo", {}, "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert outcome == True
    assert details == None

def test_check_dict_has_not_key_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_not_key("foo", {"foo": 42}, "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert outcome == False
    assert details == None

def test_check_dict_has_int_success(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_int("foo", {"foo": 21}))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert "int" in description
    assert outcome == True
    assert "21" in details

def test_check_dict_has_int_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_has_int("foo", {"foo": 21.1}))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description
    assert "int" in description
    assert outcome == False
    assert "float" in details

def test_check_dict_value_success(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_value("foo", {"foo": 42}, 42, lcc.check_eq))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description and "42" in description
    assert outcome == True
    assert details == None

def test_check_dict_value_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_dict_value("foo", {"foo": 21}, 42, lcc.check_eq))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description and "42" in description
    assert outcome == False
    assert "21" in details

# for all checkers combination with check_dict_value, only test 
# a passing and non passing case with check_str_eq

def test_check_dict_value_str_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.check_dictval_str_eq("foo", {"foo": "bar"}, "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description and "'bar'" in description
    assert outcome == True
    assert details == None

def test_check_dict_value_str_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_dictval_str_eq("foo", {"foo": "baz"}, "bar"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "foo" in description and "'bar'" in description
    assert outcome == False
    assert "'baz'" in details

###
# test that all checkers are properly generated dynamically:
# - typed checkers
# - dict value checkers
###

def test_checkers_availability():
    from lemoncheesecake import checkers as lcc_checkers
    
    types = {
        "int": ("eq", "not_eq", "gt", "gteq", "lt", "lteq"),
        "float": ("eq", "not_eq", "gt", "gteq", "lt", "lteq"),
        "str": ("eq", "not_eq"),
        "bool": ("eq",),
        "dict": (),
        "list": ()
    }
    
    for type_, comparators in types.items():
        for prefix in "check", "assert":
            checker_name = "%s_dict_has_%s" % (prefix, type_)
            assert checker_name in lcc_checkers.__all__
            assert type(getattr(lcc_checkers, checker_name)) == FunctionType
        for comparator in comparators:
            for prefix in "check", "assert", "check_dictval", "assert_dictval":
                checker_name = "%s_%s_%s" % (prefix, type_, comparator)
                assert checker_name in lcc_checkers.__all__
                assert type(getattr(lcc_checkers, checker_name)) == FunctionType

###
# assert
###

def test_assert_eq_success(reporting_session):
    run_func_in_test(lambda: lcc.assert_eq("param", "foo", "foo"))
    description, outcome, details = reporting_session.get_last_check()
    
    assert "param" in description and "foo" in description
    assert outcome == True
    assert details == None
    assert reporting_session.get_error_log_nb() == 0

def test_assert_eq_failure(reporting_session):
    run_func_in_test(lambda: lcc.assert_eq("param", "bar", "foo"))
    description, outcome, details = reporting_session.get_last_check()
     
    assert "param" in description and "foo" in description
    assert outcome == False
    assert "bar" in details
    assert reporting_session.get_error_log_nb() == 1
