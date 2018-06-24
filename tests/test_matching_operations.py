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


def test_check_that_entry(runtime_mock):
    ret = check_that_entry("foo", equal_to("bar"), in_={"foo": "bar"})
    assert ret
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "bar" in details


def test_check_that_in(runtime_mock):
    check_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    description, outcome, details = get_mocked_logged_checks()[0]
    assert "foo" in description and "1" in description
    assert outcome is True
    assert "1" in details

    description, outcome, details = get_mocked_logged_checks()[1]
    assert "bar" in description and "2" in description
    assert outcome is True
    assert "2" in details


def test_check_that_in_with_base_key(runtime_mock):
    check_that_in({"foo": {"bar": "baz"}}, "bar", equal_to("baz"), base_key=["foo"])
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_check_that_in_with_list_and_base_key(runtime_mock):
    check_that_in({"foo": {"bar": "baz"}}, ["bar"], equal_to("baz"), base_key=["foo"])
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_check_that_in_with_tuple_and_base_key(runtime_mock):
    check_that_in({"foo": {"bar": "baz"}}, ("bar", ), equal_to("baz"), base_key=["foo"])

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_require_that_in(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        require_that_in({"foo": 2, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))
    
    results = get_mocked_logged_checks()
    
    assert len(results) == 1

    description, outcome, details = results[0]

    assert "foo" in description and "1" in description
    assert outcome is False
    assert "2" in details


def test_assert_that_in(runtime_mock):
    assert_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    assert len(get_mocked_logged_checks()) == 0


def test_require_that_success(runtime_mock):
    require_that("value", "foo", equal_to("foo"))
    
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


def test_require_that_entry(runtime_mock):
    require_that_entry("foo", equal_to("bar"), in_={"foo": "bar"})

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "bar" in details


def test_assert_that_success(runtime_mock):
    assert_that("value", "foo", equal_to("foo"))

    assert len(get_mocked_logged_checks()) == 0


def test_assert_that_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that("value", "bar", equal_to("foo"))

    description, outcome, details = get_last_mocked_logged_check()

    assert "value" in description and "foo" in description
    assert outcome is False
    assert "bar" in details


def test_assert_that_entry_success(runtime_mock):
    assert_that_entry("foo", equal_to("bar"), in_={"foo": "bar"})

    assert len(get_mocked_logged_checks()) == 0


def test_assert_that_entry_failure(runtime_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that_entry("foo", equal_to("bar"), in_={"foo": "baz"})

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is False
    assert "baz" in details


def test_this_dict(runtime_mock):
    with this_dict({"foo": "bar"}):
        check_that_entry("foo", equal_to("bar"))
    
    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "bar" in details


def test_this_dict_multiple(runtime_mock):
    with this_dict({"foo": "bar"}):
        check_that_entry("foo", equal_to("bar"))
    with this_dict({"foo": "baz"}):
        check_that_entry("foo", equal_to("baz"))

    description, outcome, details = get_mocked_logged_checks()[0]
    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "bar" in details

    description, outcome, details = get_mocked_logged_checks()[1]
    assert "foo" in description and "baz" in description
    assert outcome is True
    assert "baz" in details


def test_this_dict_imbricated(runtime_mock):
    with this_dict({"foo": "bar"}):
        check_that_entry("foo", equal_to("bar"))
        with this_dict({"foo": "baz"}):
            check_that_entry("foo", equal_to("baz"))
    with this_dict({"foo": "foo"}):
        check_that_entry("foo", equal_to("foo"))

    assert all(outcome for _, outcome, _ in get_mocked_logged_checks())


def test_this_dict_using_base_key(runtime_mock):
    with this_dict({"foo": {"bar": "baz"}}).using_base_key("foo"):
        check_that_entry("bar", equal_to("baz"))

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_this_dict_using_base_key_as_list(runtime_mock):
    with this_dict({"foo": {"bar": "baz"}}).using_base_key(["foo"]):
        check_that_entry("bar", equal_to("baz"))

    description, outcome, details = get_last_mocked_logged_check()

    assert "foo" in description and "bar" in description
    assert outcome is True
    assert "baz" in details


def test_unicode(runtime_mock):
    check_that(u"ééé", u"éééààà", starts_with(u"ééé"))
    
    description, outcome, details = get_last_mocked_logged_check()

    assert u"ééé" in description
    assert outcome is True
    assert u"éééààà" in details
