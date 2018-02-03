# -*- coding: utf-8 -*-

from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_is_dict_success():
    assert_match_success(is_dict(), {}, "{}")


def test_is_dict_failure():
    assert_match_failure(is_dict(), "foo", "foo")


def test_is_float_success():
    assert_match_success(is_float(), 1.2, "1.2")


def test_is_float_failure():
    assert_match_failure(is_float(), 1, "1")


def test_is_integer_success():
    assert_match_success(is_integer(), 1, "1")


def test_is_integer_failure():
    assert_match_failure(is_integer(), 1.2, "1.2")


def test_is_bool_success():
    assert_match_success(is_bool(), True, "true")


def test_is_bool_failure():
    assert_match_failure(is_bool(), 1, "1")


def test_is_list_success():
    assert_match_success(is_list(), [], "[]")


def test_is_list_with_tuple_success():
    assert_match_success(is_list(), (), "[]")


def test_is_list_failure():
    assert_match_failure(is_list(), "foo", "foo")


def test_is_str_success():
    assert_match_success(is_str(), "foo", "foo")


def test_is_str_with_unicode_success():
    assert_match_success(is_str(), u"ààà", u"ààà")


def test_is_str_failure():
    assert_match_failure(is_str(), 1, "1")
