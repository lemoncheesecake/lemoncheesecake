# -*- coding: utf-8 -*-

from callee import Contains

from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_is_dict_success():
    assert_match_success(is_dict(), {}, Contains("{}"))


def test_is_dict_failure():
    assert_match_failure(is_dict(), "foo", Contains("foo"))


def test_is_dict_with_argument_success():
    assert_match_success(is_dict(has_entry("foo")), {"foo": 1}, Contains("1"))


def test_is_float_success():
    assert_match_success(is_float(), 1.2, Contains("1.2"))


def test_is_float_failure():
    assert_match_failure(is_float(), 1, Contains("1"))


def test_is_float_with_arg_success():
    assert_match_success(is_float(1.2), 1.2, Contains("1.2"))


def test_is_integer_success():
    assert_match_success(is_integer(), 1, Contains("1"))


def test_is_integer_failure():
    assert_match_failure(is_integer(), 1.2, Contains("1.2"))


def test_is_integer_with_arg_success():
    assert_match_success(is_integer(1), 1, Contains("1"))


def test_is_bool_success():
    assert_match_success(is_bool(), True, Contains("true"))


def test_is_bool_failure():
    assert_match_failure(is_bool(), 1, Contains("1"))


def test_is_bool_with_arg_success():
    assert_match_success(is_bool(True), True, Contains("true"))


def test_is_list_success():
    assert_match_success(is_list(), [], Contains("[]"))


def test_is_list_with_tuple_success():
    assert_match_success(is_list(), (), Contains("[]"))


def test_is_list_failure():
    assert_match_failure(is_list(), "foo", Contains("foo"))


def test_is_list_with_arg_success():
    assert_match_success(is_list(has_length(2)), [21, 42], Contains("2"))


def test_is_str_success():
    assert_match_success(is_str(), "foo", Contains("foo"))


def test_is_str_with_unicode_success():
    assert_match_success(is_str(), "ààà", Contains("ààà"))


def test_is_str_failure():
    assert_match_failure(is_str(), 1, Contains("1"))


def test_is_str_with_arg_success():
    assert_match_success(is_str("foo"), "foo", Contains("foo"))
