'''
Created on Dec 1, 2016

@author: nicolas
'''

import re
from types import FunctionType

import lemoncheesecake.api as lcc

from helpers.runner import run_func_in_test
from helpers.report import get_last_logged_check, count_logs


###
# check_eq
###

def test_check_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_eq("param", "foo", "foo"))
    )

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_eq("param", "bar", "foo"))
    )

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details


###
# check_not_eq
###

def test_check_not_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_not_eq("param", "bar", "foo"))
    )

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_check_not_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_not_eq("param", "foo", "foo"))
    )

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "foo" in check.details


###
# check_gt & check_gteq
###

def test_check_gt_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_gt("param", 42, 21))
    )

    assert check.outcome is True
    assert "42" in check.details


def test_check_gt_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_gt("param", 21, 21))
    )

    assert check.outcome is False
    assert "21" in check.details


def test_check_gteq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_gteq("param", 21, 21))
    )

    assert check.outcome is True
    assert "21" in check.details


def test_check_gteq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_gteq("param", 20, 21))
    )

    assert check.outcome is False
    assert "20" in check.details


###
# check_lt & check_lteq
###

def test_check_lt_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_lt("param", 21, 42))
    )

    assert check.outcome == True
    assert "21" in check.details


def test_check_lt_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_lt("param", 21, 21))
    )

    assert check.outcome is False
    assert "21" in check.details


def test_check_lteq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_lteq("param", 21, 21))
    )

    assert check.outcome is True
    assert "21" in check.details


def test_check_lteq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_lteq("param", 21, 20))
    )

    assert check.outcome is False
    assert "21" in check.details


###
# check_str_eq & check_str_not_eq
###

def test_check_str_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_eq("param", "foo", "foo"))
    )

    assert "param" in check.description and "'foo'" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_str_eq_failure():
    check = get_last_logged_check(run_func_in_test(lambda: lcc.check_str_eq("param", "bar", "foo")))

    assert "param" in check.description and "'foo'" in check.description
    assert check.outcome is False
    assert "'bar'" in check.details


def test_check_str_not_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_not_eq("param", "bar", "foo"))
    )

    assert "param" in check.description and "'foo'" in check.description
    assert check.outcome is True
    assert "'bar'" in check.details


def test_check_str_not_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_not_eq("param", "foo", "foo"))
    )

    assert "param" in check.description and "'foo'" in check.description
    assert check.outcome is False
    assert "'foo'" in check.details


###
# check_str_match & check_str_does_not_match
###

def test_check_str_match_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_match("param", "foo", re.compile("^f")))
    )

    assert "param" in check.description and "'^f'" in check.description
    assert check.outcome is True
    assert "'foo'" in check.details


def test_check_str_match_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_match("param", "bar", re.compile("^f")))
    )

    assert "param" in check.description and "'^f'" in check.description
    assert check.outcome is False
    assert "'bar'" in check.details


def test_check_str_does_not_match_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_does_not_match("param", "bar", re.compile("^f")))
    )

    assert "param" in check.description and "'^f'" in check.description
    assert check.outcome is True
    assert "'bar'" in check.details


def test_check_str_does_not_match_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_does_not_match("param", "foo", re.compile("^f")))
    )

    assert "param" in check.description and "'^f'" in check.description
    assert check.outcome is False
    assert "'foo'" in check.details


###
# check_str_contains & check_str_does_not_contain
###

def test_check_str_contains_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_contains("param", "foobar", "bar"))
    )

    assert "param" in check.description and "'bar'" in check.description
    assert check.outcome is True
    assert "'foobar'" in check.details


def test_check_str_contains_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_contains("param", "foobaz", "bar"))
    )

    assert "param" in check.description and "'bar'" in check.description
    assert check.outcome is False
    assert "'foobaz'" in check.details


def test_check_str_does_not_contain_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_does_not_contain("param", "foobaz", "bar"))
    )

    assert "param" in check.description and "'bar'" in check.description
    assert check.outcome is True
    assert "'foobaz'" in check.details


def test_check_str_does_not_contains_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_str_does_not_contain("param", "foobar", "bar"))
    )

    assert "param" in check.description and "'bar'" in check.description
    assert check.outcome is False
    assert "'foobar'" in check.details


###
# Typed checkers
###

def test_check_int_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_int_eq("param", 1, 1))
    )

    assert "int" in check.description and "1" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_int_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_int_eq("param", 1.0, 1))
    )

    assert "int" in check.description and "1" in check.description
    assert check.outcome is False
    assert "float" in check.details and "1.0" in check.details


def test_check_float_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_float_eq("param", 1.0, 1.0))
    )

    assert "float" in check.description and "1.0" in check.description
    assert check.outcome is True
    assert check.details == None


def test_check_float_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_float_eq("param", 1, 1.0))
    )

    assert "float" in check.description and "1.0" in check.description
    assert check.outcome is False
    assert "int" in check.details and "1" in check.details


def test_check_bool_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_bool_eq("param", False, False))
    )

    assert "bool" in check.description and "False" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_bool_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_bool_eq("param", 0, False))
    )

    assert "bool" in check.description and "False" in check.description
    assert check.outcome is False
    assert "int" in check.details and "0" in check.details


def test_check_typed_eq_none_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_int_eq("param", None, None))
    )

    assert "int" not in check.description and "None" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_typed_eq_none_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_int_eq("param", 42, None))
    )

    assert "int" not in check.description and "None" in check.description
    assert check.outcome is False
    assert "42" in check.details and "int" in check.details


###
# list checkers
###

def test_check_list_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_list_len("param", (1, 2, 3), 3))
    )

    assert "param" in check.description and "3" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_list_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_list_len("param", (1, 2), 3))
    )

    assert "param" in check.description and "3" in check.description
    assert check.outcome is False
    assert "(1, 2)" in check.details


def test_check_list_contains_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_list_contains("param", ("foo", "bar"), ("bar", )))
    )

    assert "param" in check.description and "bar" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_list_contains_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_list_contains("param", ("foo", "baz"), ("bar", )))
    )

    assert "param" in check.description and "bar" in check.description
    assert check.outcome is False
    assert check.details is not None


def test_check_choice_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_choice("param", "foo", ("foo", "bar")))
    )

    assert "param" in check.description and "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert check.details is not None


def test_check_choice_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_choice("param", "baz", ("foo", "bar")))
    )

    assert "param" in check.description and "foo" in check.description and "bar" in check.description
    assert check.outcome is False
    assert check.details is not None


###
# dict checkers
# TODO: key_label and show_actual arguments are not yet tested
###

def test_check_dict_has_key_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_key("foo", {"foo": 42}, "foo"))
    )

    assert "foo" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_dict_has_key_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_key("foo", {"bar": 42}, "foo"))
    )

    assert "foo" in check.description
    assert check.outcome is False
    assert check.details is None


def test_check_dict_has_not_key_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_not_key("foo", {}, "foo"))
    )

    assert "foo" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_dict_has_not_key_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_not_key("foo", {"foo": 42}, "foo"))
    )

    assert "foo" in check.description
    assert check.outcome is False
    assert check.details is None


def test_check_dict_has_int_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_int("foo", {"foo": 21}))
    )

    assert "foo" in check.description
    assert "int" in check.description
    assert check.outcome is True
    assert "21" in check.details


def test_check_dict_has_int_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_has_int("foo", {"foo": 21.1}))
    )

    assert "foo" in check.description
    assert "int" in check.description
    assert check.outcome is False
    assert "float" in check.details


def test_check_dict_value_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_value("foo", {"foo": 42}, 42, lcc.check_eq))
    )

    assert "foo" in check.description and "42" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_dict_value_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dict_value("foo", {"foo": 21}, 42, lcc.check_eq))
    )

    assert "foo" in check.description and "42" in check.description
    assert check.outcome is False
    assert "21" in check.details


# for all checkers combination with check_dict_value, only test
# a passing and non passing case with check_str_eq

def test_check_dict_value_str_eq_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dictval_str_eq("foo", {"foo": "bar"}, "bar"))
    )

    assert "foo" in check.description and "'bar'" in check.description
    assert check.outcome is True
    assert check.details is None


def test_check_dict_value_str_eq_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_dictval_str_eq("foo", {"foo": "baz"}, "bar"))
    )

    assert "foo" in check.description and "'bar'" in check.description
    assert check.outcome is False
    assert "'baz'" in check.details


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

def test_assert_eq_success():
    report = run_func_in_test(lambda: lcc.assert_eq("param", "foo", "foo"))
    check = get_last_logged_check(report)

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is True
    assert check.details is None
    assert count_logs(report, "error") == 0


def test_assert_eq_failure():
    report = run_func_in_test(lambda: lcc.assert_eq("param", "bar", "foo"))
    check = get_last_logged_check(report)

    assert "param" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details
    assert count_logs(report, "error") == 1
