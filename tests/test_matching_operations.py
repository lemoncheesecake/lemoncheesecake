# -*- coding: utf-8 -*-

'''
Created on Dec 1, 2016

@author: nicolas
'''

import lemoncheesecake.api as lcc

from helpers.runner import run_func_in_test
from helpers.report import get_last_logged_check, assert_last_test_status, get_last_test, \
    assert_test_has_error_log, assert_test_checks


def test_check_that_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_that("value", "foo", lcc.equal_to("foo")))
    )

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is True
    assert "foo" in check.details


def test_check_that_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_that("value", "bar", lcc.equal_to("foo")))
    )

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details


def test_check_that_entry():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))
    )

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_require_that_success():
    marker = []
    def test():
        marker.append("before_test")
        lcc.require_that("value", "foo", lcc.equal_to("foo"))
        marker.append("after_test")
    check = get_last_logged_check(run_func_in_test(test))

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is True
    assert "foo" in check.details
    assert marker == ["before_test", "after_test"]


def test_require_that_failure():
    marker = []
    def test():
        marker.append("before_test")
        lcc.require_that("value", "bar", lcc.equal_to("foo"))
        marker.append("after_test")
    report = run_func_in_test(test)
    check = get_last_logged_check(report)

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details
    assert marker == ["before_test"]


def test_require_that_entry():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.require_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))
    )

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_assert_that_success():
    report = run_func_in_test(lambda: lcc.assert_that("value", "foo", lcc.equal_to("foo")))
    assert_last_test_status(report, "passed")


def test_assert_that_failure():
    marker = []
    def test():
        marker.append("before_test")
        lcc.assert_that("value", "bar", lcc.equal_to("foo"))
        marker.append("after_test")
    report = run_func_in_test(test)
    check = get_last_logged_check(report)

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details
    assert marker == ["before_test"]
    assert_test_has_error_log(get_last_test(report))


def test_assert_that_entry_success():
    report = run_func_in_test(lambda: lcc.assert_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))
    test = get_last_test(report)
    assert len(test.steps) == 0


def test_assert_that_entry_failure():
    report = run_func_in_test(lambda: lcc.assert_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "baz"}))
    assert_last_test_status(report, "failed")


def test_this_dict():
    def func():
        with lcc.this_dict({"foo": "bar"}):
            lcc.check_that_entry("foo", lcc.equal_to("bar"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_this_dict_multiple():
    def func():
        with lcc.this_dict({"foo": "bar"}):
            lcc.check_that_entry("foo", lcc.equal_to("bar"))
        with lcc.this_dict({"foo": "baz"}):
            lcc.check_that_entry("foo", lcc.equal_to("baz"))

    test = get_last_test(run_func_in_test(func))
    assert_test_checks(test, expected_successes=2)


def test_this_dict_imbricated():
    def func():
        with lcc.this_dict({"foo": "bar"}):
            lcc.check_that_entry("foo", lcc.equal_to("bar"))
            with lcc.this_dict({"foo": "baz"}):
                lcc.check_that_entry("foo", lcc.equal_to("baz"))
        with lcc.this_dict({"foo": "foo"}):
            lcc.check_that_entry("foo", lcc.equal_to("foo"))

    test = get_last_test(run_func_in_test(func))
    assert_test_checks(test, expected_successes=3)


def test_this_dict_using_base_key():
    def func():
        with lcc.this_dict({"foo": {"bar": "baz"}}).using_base_key("foo"):
            lcc.check_that_entry("bar", lcc.equal_to("baz"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome == True
    assert "baz" in check.details


def test_this_dict_using_base_key_as_list():
    def func():
        with lcc.this_dict({"foo": {"bar": "baz"}}).using_base_key(["foo"]):
            lcc.check_that_entry("bar", lcc.equal_to("baz"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome == True
    assert "baz" in check.details


def test_unicode():
    check = get_last_logged_check(
        run_func_in_test(lambda: lcc.check_that(u"ééé", u"éééààà", lcc.starts_with(u"ééé")))
    )

    assert u"ééé" in check.description
    assert check.outcome == True
    assert u"éééààà" in check.details
