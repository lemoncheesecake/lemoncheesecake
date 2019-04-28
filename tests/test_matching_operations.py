# -*- coding: utf-8 -*-

'''
Created on Dec 1, 2016

@author: nicolas
'''

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

import pytest

from helpers.runtime import runtime_mock, get_last_mocked_logged_check, get_mocked_logged_checks


def test_check_that_success(runtime_mock):
    ret = check_that("value", "foo", equal_to("foo"))
    assert ret

    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is True
    assert "foo" in details


def test_check_that_failure(runtime_mock):
    ret = check_that("value", "bar", equal_to("foo"))
    assert not ret

    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is False
    assert "bar" in details


def test_check_that_in(runtime_mock):
    results = check_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    assert all(results)

    description, outcome, details = get_mocked_logged_checks()[0]
    assert "foo" in description and "1" in description
    assert outcome is True
    assert "1" in details

    description, outcome, details = get_mocked_logged_checks()[1]
    assert "bar" in description and "2" in description
    assert outcome is True
    assert "2" in details


def test_check_that_in_with_base_key(runtime_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, "bar", equal_to("baz"), base_key=["foo"])

    assert all(results)
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_check_that_in_with_list_and_base_key(runtime_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, ["bar"], equal_to("baz"), base_key=["foo"])

    assert all(results)
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_check_that_in_with_tuple_and_base_key(runtime_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, ("bar", ), equal_to("baz"), base_key=["foo"])

    assert all(results)

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_require_that_in_success(runtime_mock):
    require_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    mock_results = get_mocked_logged_checks()

    assert len(mock_results) == 2
    assert all(mock_results)


def test_require_that_in_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        require_that_in({"foo": 2, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    mock_results = get_mocked_logged_checks()
    
    assert len(mock_results) == 1

    description, outcome, details = mock_results[0]

    assert "foo" in description and "1" in description
    assert outcome is False
    assert "2" in details


def test_assert_that_in_success(runtime_mock):
    results = assert_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    assert all(results)
    assert len(get_mocked_logged_checks()) == 0


def test_assert_that_in_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that_in({"foo": "baz"}, "foo", equal_to("bar"))

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is False
    assert "baz" in details


def test_require_that_success(runtime_mock):
    result = require_that("value", "foo", equal_to("foo"))
    assert result
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is True
    assert "foo" in details


def test_require_that_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        require_that("value", "bar", equal_to("foo"))
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is False
    assert "bar" in details


def test_assert_that_success(runtime_mock):
    result = assert_that("value", "foo", equal_to("foo"))
    assert result

    assert len(get_mocked_logged_checks()) == 0


def test_assert_that_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that("value", "bar", equal_to("foo"))

    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is False
    assert "bar" in details


def test_unicode(runtime_mock):
    result = check_that(u"ééé", u"éééààà", starts_with(u"ééé"))
    assert result
    
    description, outcome, details = get_last_mocked_logged_check()

    assert u"ééé" in description
    assert outcome is True
    assert u"éééààà" in details
