# -*- coding: utf-8 -*-

'''
Created on Dec 1, 2016

@author: nicolas
'''

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

import pytest
from callee import Any

from helpers.matching import log_check_mock
from helpers.utils import Search


def test_check_that_success(log_check_mock):
    ret = check_that("value", "foo", equal_to("foo"))
    assert ret

    log_check_mock.assert_called_once_with(Search("value.+foo"), True, Search("foo"))


def test_check_that_failure(log_check_mock):
    ret = check_that("value", "bar", equal_to("foo"))
    assert not ret

    log_check_mock.assert_called_once_with(Search("value.+foo"), False, Search("bar"))


def test_check_that_quiet(log_check_mock):
    check_that("value", "bar", equal_to("foo"), quiet=True)

    log_check_mock.assert_called_once_with(Any(), Any(), None)


def test_check_that_in(log_check_mock):
    results = check_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    assert all(results)

    log_check_mock.assert_any_call(Search("foo.+1"), True, Search("1"))
    log_check_mock.assert_any_call(Search("bar.+2"), True, Search("2"))


def test_check_that_in_with_base_key(log_check_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, "bar", equal_to("baz"), base_key=["foo"])

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_list_and_base_key(log_check_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, ["bar"], equal_to("baz"), base_key=["foo"])

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_tuple_and_base_key(log_check_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, ("bar", ), equal_to("baz"), base_key=["foo"])

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_tuple_and_list_index(log_check_mock):
    results = check_that_in({"foo": [{"bar": "baz"}]}, ("foo", 0, "bar"), equal_to("baz"))

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+0.+bar"), True, Search("baz"))


def test_check_that_in_with_expected_as_dict(log_check_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, {"foo": {"bar": equal_to("baz")}})

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_expected_as_dict_with_list(log_check_mock):
    results = check_that_in({"foo": [{"bar": "baz"}]}, {"foo": [{"bar": equal_to("baz")}]})

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_expected_as_dict_and_base_key(log_check_mock):
    results = check_that_in({"foo": {"bar": "baz"}}, {"bar": equal_to("baz")}, base_key=("foo",))

    assert all(results)

    log_check_mock.assert_called_once_with(Search("foo.+bar"), True, Search("baz"))


def test_check_that_in_with_expected_as_dict_multiple(log_check_mock):
    results = check_that_in({"foo": {"bar": 1, "baz": 2}}, {"foo": {"bar": equal_to(1), "baz": equal_to(2)}})

    assert all(results)

    log_check_mock.assert_any_call(Search("foo.+bar"), True, Search("1"))
    log_check_mock.assert_any_call(Search("foo.+baz"), True, Search("2"))


def test_check_that_in_quiet(log_check_mock):
    check_that_in({"foo": "bar"}, "foo", equal_to("bar"), quiet=True)

    log_check_mock.assert_called_once_with(Any(), Any(), None)


def test_require_that_in_success(log_check_mock):
    require_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    log_check_mock.assert_any_call(Search("foo.+1"), True, Any())
    log_check_mock.assert_any_call(Search("bar.+2"), True, Any())


def test_require_that_in_failure(log_check_mock):
    with pytest.raises(lcc.AbortTest):
        require_that_in({"foo": 2, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    log_check_mock.assert_called_once_with(Search("foo.+1"), False, Search("2"))


def test_assert_that_in_success(log_check_mock):
    results = assert_that_in({"foo": 1, "bar": 2}, "foo", equal_to(1), "bar", equal_to(2))

    assert all(results)

    log_check_mock.assert_not_called()


def test_assert_that_in_failure(log_check_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that_in({"foo": "baz"}, "foo", equal_to("bar"))

    log_check_mock.assert_called_once_with(Search("foo.+bar"), False, Search("baz"))


def test_require_that_success(log_check_mock):
    result = require_that("value", "foo", equal_to("foo"))
    assert result

    log_check_mock.assert_called_once_with(Search("value.+foo"), True, Search("foo"))


def test_require_that_failure(log_check_mock):
    with pytest.raises(lcc.AbortTest):
        require_that("value", "bar", equal_to("foo"))

    log_check_mock.assert_called_once_with(Search("value.+foo"), False, Search("bar"))


def test_require_that_quiet(log_check_mock):
    require_that("value", "foo", equal_to("foo"), quiet=True)

    log_check_mock.assert_called_once_with(Any(), Any(), None)


def test_assert_that_success(log_check_mock):
    result = assert_that("value", "foo", equal_to("foo"))
    assert result

    log_check_mock.assert_not_called()


def test_assert_that_failure(log_check_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that("value", "bar", equal_to("foo"))

    log_check_mock.assert_called_once_with(Search("value.+foo"), False, Search("bar"))


def test_assert_that_quiet(log_check_mock):
    with pytest.raises(lcc.AbortTest):
        assert_that("value", "bar", equal_to("foo"), quiet=True)

    log_check_mock.assert_called_once_with(Any(), Any(), None)


def test_unicode(log_check_mock):
    result = check_that("ééé", "éééààà", starts_with("ééé"))
    assert result

    log_check_mock.assert_called_once_with(Search("ééé"), True, Search("éééààà"))
