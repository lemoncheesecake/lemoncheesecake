# -*- coding: utf-8 -*-

'''
Created on Dec 1, 2016

@author: nicolas
'''

import lemoncheesecake.api as lcc

from helpers import reporting_session, run_func_in_test

def test_check_that_success(reporting_session):
    run_func_in_test(lambda: lcc.check_that("value", "foo", lcc.equal_to("foo")))
    description, outcome, details = reporting_session.get_last_check()

    assert "value" in description and "foo" in description
    assert outcome == True
    assert "foo" in details

def test_check_that_failure(reporting_session):
    run_func_in_test(lambda: lcc.check_that("value", "bar", lcc.equal_to("foo")))
    description, outcome, details = reporting_session.get_last_check()

    assert "value" in description and "foo" in description
    assert outcome == False
    assert "bar" in details

def test_check_that_entry(reporting_session):
    run_func_in_test(lambda: lcc.check_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))
    description, outcome, details = reporting_session.get_last_check()

    assert "foo" in description and "bar" in description
    assert outcome == True
    assert "bar" in details

def test_require_that_success(reporting_session):
    marker = []
    def test():
        marker.append("before_test")
        lcc.require_that("value", "foo", lcc.equal_to("foo"))
        marker.append("after_test")
    run_func_in_test(test)
    description, outcome, details = reporting_session.get_last_check()

    assert "value" in description and "foo" in description
    assert outcome == True
    assert "foo" in details
    assert marker == ["before_test", "after_test"]

def test_require_that_failure(reporting_session):
    marker = []
    def test():
        marker.append("before_test")
        lcc.require_that("value", "bar", lcc.equal_to("foo"))
        marker.append("after_test")
    run_func_in_test(test)
    description, outcome, details = reporting_session.get_last_check()

    assert "value" in description and "foo" in description
    assert outcome == False
    assert "bar" in details
    assert marker == ["before_test"]
    assert reporting_session.get_error_log_nb() == 1

def test_require_that_entry(reporting_session):
    run_func_in_test(lambda: lcc.require_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))
    description, outcome, details = reporting_session.get_last_check()

    assert "foo" in description and "bar" in description
    assert outcome == True
    assert "bar" in details

def test_assert_that_success(reporting_session):
    run_func_in_test(lambda: lcc.assert_that("value", "foo", lcc.equal_to("foo")))

    assert reporting_session.check_nb == 0

def test_assert_that_failure(reporting_session):
    marker = []
    def test():
        marker.append("before_test")
        lcc.assert_that("value", "bar", lcc.equal_to("foo"))
        marker.append("after_test")
    run_func_in_test(test)
    description, outcome, details = reporting_session.get_last_check()

    assert "value" in description and "foo" in description
    assert outcome == False
    assert "bar" in details
    assert marker == ["before_test"]
    assert reporting_session.get_error_log_nb() == 1

def test_assert_that_entry_success(reporting_session):
    run_func_in_test(lambda: lcc.assert_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "bar"}))

    assert reporting_session.check_nb == 0

def test_assert_that_entry_failure(reporting_session):
    run_func_in_test(lambda: lcc.assert_that_entry("foo", lcc.equal_to("bar"), in_={"foo": "baz"}))

    description, outcome, details = reporting_session.get_last_check()
    assert outcome == False

def test_unicode(reporting_session):
    run_func_in_test(lambda: lcc.check_that(u"ééé", u"éééààà", lcc.starts_with(u"ééé")))
    description, outcome, details = reporting_session.get_last_check()

    assert u"ééé" in description
    assert outcome == True
    assert u"éééààà" in details
