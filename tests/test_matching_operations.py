# -*- coding: utf-8 -*-

'''
Created on Dec 1, 2016

@author: nicolas
'''

from lemoncheesecake.matching import *

from helpers.runner import run_func_in_test
from helpers.report import get_last_logged_check, get_last_test_checks, assert_last_test_status, get_last_test, \
    count_logs, assert_test_checks


def test_check_that_success():
    check = get_last_logged_check(
        run_func_in_test(lambda: check_that("value", "foo", equal_to("foo")))
    )

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is True
    assert "foo" in check.details


def test_check_that_failure():
    check = get_last_logged_check(
        run_func_in_test(lambda: check_that("value", "bar", equal_to("foo")))
    )

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details


def test_check_that_entry():
    check = get_last_logged_check(
        run_func_in_test(lambda: check_that_entry("foo", equal_to("bar"), in_={"foo": "bar"}))
    )

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_check_that_in():
    checks = get_last_test_checks(
        run_func_in_test(
            lambda: check_that_in(
                {"foo": 1, "bar": 2},
                "foo", equal_to(1),
                "bar", equal_to(2)
            )
        )
    )

    assert "foo" in checks[0].description and "1" in checks[0].description
    assert checks[0].outcome is True
    assert "1" in checks[0].details

    assert "bar" in checks[1].description and "2" in checks[1].description
    assert checks[1].outcome is True
    assert "2" in checks[1].details


def test_check_that_in_with_base_key():
    check = get_last_logged_check(
        run_func_in_test(
            lambda: check_that_in(
                {"foo": {"bar": "baz"}},
                "bar", equal_to("baz"),
                base_key=["foo"]
            )
        )
    )

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "baz" in check.details


def test_require_that_in():
    checks = get_last_test_checks(
        run_func_in_test(
            lambda: require_that_in(
                {"foo": 2, "bar": 2},
                "foo", equal_to(1),
                "bar", equal_to(2)
            )
        )
    )

    assert len(checks) == 1

    assert "foo" in checks[0].description and "1" in checks[0].description
    assert checks[0].outcome is False
    assert "2" in checks[0].details


def test_assert_that_in():
    checks = get_last_test_checks(
        run_func_in_test(
            lambda: assert_that_in(
                {"foo": 1, "bar": 2},
                "foo", equal_to(1),
                "bar", equal_to(2)
            )
        )
    )

    assert len(checks) == 0


def test_require_that_success():
    marker = []
    def test():
        marker.append("before_test")
        require_that("value", "foo", equal_to("foo"))
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
        require_that("value", "bar", equal_to("foo"))
        marker.append("after_test")
    report = run_func_in_test(test)
    check = get_last_logged_check(report)

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details
    assert marker == ["before_test"]


def test_require_that_entry():
    check = get_last_logged_check(
        run_func_in_test(lambda: require_that_entry("foo", equal_to("bar"), in_={"foo": "bar"}))
    )

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_assert_that_success():
    report = run_func_in_test(lambda: assert_that("value", "foo", equal_to("foo")))
    assert_last_test_status(report, "passed")


def test_assert_that_failure():
    marker = []
    def test():
        marker.append("before_test")
        assert_that("value", "bar", equal_to("foo"))
        marker.append("after_test")
    report = run_func_in_test(test)
    check = get_last_logged_check(report)

    assert "value" in check.description and "foo" in check.description
    assert check.outcome is False
    assert "bar" in check.details
    assert marker == ["before_test"]
    assert count_logs(report, "error") == 1


def test_assert_that_entry_success():
    report = run_func_in_test(lambda: assert_that_entry("foo", equal_to("bar"), in_={"foo": "bar"}))
    test = get_last_test(report)
    assert len(test.steps) == 0


def test_assert_that_entry_failure():
    report = run_func_in_test(lambda: assert_that_entry("foo", equal_to("bar"), in_={"foo": "baz"}))
    assert_last_test_status(report, "failed")


def test_this_dict():
    def func():
        with this_dict({"foo": "bar"}):
            check_that_entry("foo", equal_to("bar"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "bar" in check.details


def test_this_dict_multiple():
    def func():
        with this_dict({"foo": "bar"}):
            check_that_entry("foo", equal_to("bar"))
        with this_dict({"foo": "baz"}):
            check_that_entry("foo", equal_to("baz"))

    test = get_last_test(run_func_in_test(func))
    assert_test_checks(test, expected_successes=2)


def test_this_dict_imbricated():
    def func():
        with this_dict({"foo": "bar"}):
            check_that_entry("foo", equal_to("bar"))
            with this_dict({"foo": "baz"}):
                check_that_entry("foo", equal_to("baz"))
        with this_dict({"foo": "foo"}):
            check_that_entry("foo", equal_to("foo"))

    test = get_last_test(run_func_in_test(func))
    assert_test_checks(test, expected_successes=3)


def test_this_dict_using_base_key():
    def func():
        with this_dict({"foo": {"bar": "baz"}}).using_base_key("foo"):
            check_that_entry("bar", equal_to("baz"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "baz" in check.details


def test_this_dict_using_base_key_as_list():
    def func():
        with this_dict({"foo": {"bar": "baz"}}).using_base_key(["foo"]):
            check_that_entry("bar", equal_to("baz"))

    check = get_last_logged_check(run_func_in_test(func))

    assert "foo" in check.description and "bar" in check.description
    assert check.outcome is True
    assert "baz" in check.details


def test_unicode():
    check = get_last_logged_check(
        run_func_in_test(lambda: check_that(u"ééé", u"éééààà", starts_with(u"ééé")))
    )

    assert u"ééé" in check.description
    assert check.outcome is True
    assert u"éééààà" in check.details
