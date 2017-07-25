'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import InvalidMetadataError, ProgrammingError, InternalError
from lemoncheesecake.utils import get_distincts_in_list, get_callable_args
from lemoncheesecake.testtree import BaseTest, BaseSuite

SUITE_HOOKS = "setup_test", "teardown_test", "setup_suite", "teardown_suite"

__all__ = (
    "Test", "Suite", "filter_suites"
)

class Test(BaseTest):
    def __init__(self, name, description, callback):
        BaseTest.__init__(self, name, description)
        self.callback = callback
        self.disabled = False

    def get_params(self):
        return get_callable_args(self.callback)

def _assert_valid_hook_name(hook_name):
    if hook_name not in SUITE_HOOKS:
        raise InternalError("Invalid hook name '%s'" % hook_name)

class Suite(BaseSuite):
    def __init__(self, obj, name, description):
        BaseSuite.__init__(self, name, description)
        self.obj = obj
        self.rank = 0
        self._hooks = {}
        self._selected_test_names = []
        self.disabled = False

    def add_hook(self, hook_name, func):
        _assert_valid_hook_name(hook_name)
        self._hooks[hook_name] = func

    def has_hook(self, hook_name):
        _assert_valid_hook_name(hook_name)
        return hook_name in self._hooks

    def get_hook(self, hook_name):
        _assert_valid_hook_name(hook_name)
        return self._hooks.get(hook_name)

    def get_hook_params(self, hook_name):
        hook = self.get_hook(hook_name)
        assert hook != None
        return get_callable_args(hook)

    def assert_test_is_unique_in_suite(self, test):
        try:
            next(t for t in self._tests if t.description == test.description)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "A test with description '%s' is already registered in test suite %s" % (test.description, self.get_path_as_str())
            )

        try:
            next(t for t in self._tests if t.name == test.name)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "A test with name '%s' is already registered in test suite %s" % (test.name, self.get_path_as_str())
            )

    def assert_sub_suite_is_unique_in_suite(self, sub_suite):
        try:
            next(s for s in self._suites if s.description == sub_suite.description)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "A sub test suite with description '%s' is already registered in test suite %s" % (sub_suite.name, self.get_path_as_str())
            )

        try:
            next(s for s in self._suites if s.name == sub_suite.name)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "A sub test suite with name '%s' is already registered in test suite %s" % (sub_suite.name, self.get_path_as_str())
            )

    def add_test(self, test):
        self.assert_test_is_unique_in_suite(test)
        BaseSuite.add_test(self, test)
        self._selected_test_names.append(test.name)

    def add_suite(self, suite):
        self.assert_sub_suite_is_unique_in_suite(suite)
        BaseSuite.add_suite(self, suite)

    def get_test(self, test_name):
        for test in self._tests:
            if test.name == test_name:
                return test
        raise ProgrammingError("unknown test '%s'" % test_name)

    def get_tests(self, filtered=True):
        tests = BaseSuite.get_tests(self)
        if filtered:
            return list(filter(self.is_test_selected, tests))
        else:
            return tests

    def get_suites(self, filtered=True):
        suites = BaseSuite.get_suites(self)
        if filtered:
            return list(filter(lambda suite: suite.has_selected_tests(deep=True), suites))
        else:
            return suites

    def get_fixtures(self, filtered=True, recursive=True):
        fixtures = []

        suite_setup = self.get_hook("setup_suite")
        if suite_setup:
            fixtures.extend(get_callable_args(suite_setup))

        for test in self.get_tests(filtered):
            fixtures.extend(test.get_params())
        if recursive:
            for sub_suite in self.get_suites(filtered):
                fixtures.extend(sub_suite.get_fixtures())

        return get_distincts_in_list(fixtures)

    ###
    # Filtering methods
    ###

    def apply_filter(self, filter):
        self._selected_test_names = [ ]

        for test in self._tests:
            if filter.match_test(test, self):
                self._selected_test_names.append(test.name)

        for suite in self._suites:
            suite.apply_filter(filter)

    def has_selected_tests(self, deep=True):
        if deep:
            if self._selected_test_names:
                return True

            for suite in self.get_suites():
                if suite.has_selected_tests():
                    return True

            return False
        else:
            return bool(self._selected_test_names)

    def is_test_selected(self, test):
        return test.name in self._selected_test_names

def filter_suites(suites, filtr):
    filtered = []
    for suite in suites:
        suite.apply_filter(filtr)
        if suite.has_selected_tests():
            filtered.append(suite)
    return filtered
