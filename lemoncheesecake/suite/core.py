'''
Created on Sep 8, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import InvalidMetadataError, InternalError
from lemoncheesecake.helpers.orderedset import OrderedSet
from lemoncheesecake.helpers.introspection import get_callable_args, get_object_attributes
from lemoncheesecake.testtree import BaseTest, BaseSuite

SUITE_HOOKS = "setup_test", "teardown_test", "setup_suite", "teardown_suite"

__all__ = (
    "Test", "Suite"
)


class Test(BaseTest):
    def __init__(self, name, description, callback):
        BaseTest.__init__(self, name, description)
        self.callback = callback
        self.disabled = False
        self.rank = 0
        self.dependencies = []

    def is_disabled(self):
        node = self
        while node is not None:
            if node.disabled:
                return True
            node = node.parent_suite
        return False

    def get_fixtures(self):
        return get_callable_args(self.callback)


def _assert_valid_hook_name(hook_name):
    if hook_name not in SUITE_HOOKS:
        raise InternalError("Invalid hook name '%s'" % hook_name)


class InjectedFixture:
    def __init__(self, fixture_name):
        self.fixture_name = fixture_name


def _load_injected_fixtures(obj):
    fixtures = {}
    for attr_name, attr in get_object_attributes(obj):
        if isinstance(attr, InjectedFixture):
            fixtures[attr.fixture_name or attr_name] = attr_name
    return fixtures


class Suite(BaseSuite):
    def __init__(self, obj, name, description):
        BaseSuite.__init__(self, name, description)
        self.obj = obj
        self.rank = 0
        self._hooks = {}
        self._injected_fixtures = _load_injected_fixtures(obj)
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
        assert hook
        return get_callable_args(hook)

    def get_injected_fixture_names(self):
        return self._injected_fixtures.keys()

    def inject_fixtures(self, fixtures):
        for fixture_name, fixture_value in fixtures.items():
            attr_name = self._injected_fixtures[fixture_name]
            setattr(self.obj, attr_name, fixture_value)

    def assert_test_is_unique_in_suite(self, test):
        if any(t for t in self._tests if t.description == test.description):
            raise InvalidMetadataError(
                "A test with description '%s' is already registered in test suite %s" % (test.description, self.path)
            )

        if any(t for t in self._tests if t.name == test.name):
            raise InvalidMetadataError(
                "A test with name '%s' is already registered in test suite %s" % (test.name, self.path)
            )

    def assert_sub_suite_is_unique_in_suite(self, sub_suite):
        if any(s for s in self._suites if s.description == sub_suite.description):
            raise InvalidMetadataError(
                "A sub test suite with description '%s' is already registered in test suite %s" % (sub_suite.name, self.path)
            )

        if any(s for s in self._suites if s.name == sub_suite.name):
            raise InvalidMetadataError(
                "A sub test suite with name '%s' is already registered in test suite %s" % (sub_suite.name, self.path)
            )

    def add_test(self, test):
        self.assert_test_is_unique_in_suite(test)
        BaseSuite.add_test(self, test)

    def add_suite(self, suite):
        self.assert_sub_suite_is_unique_in_suite(suite)
        BaseSuite.add_suite(self, suite)

    def get_fixtures(self):
        fixtures = OrderedSet(self._injected_fixtures.keys())

        suite_setup = self.get_hook("setup_suite")
        if suite_setup:
            fixtures.update(get_callable_args(suite_setup))

        return fixtures
