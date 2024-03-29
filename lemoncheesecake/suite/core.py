from typing import Dict, Iterable, Sequence

from lemoncheesecake.exceptions import SuiteLoadingError, ValidationError
from lemoncheesecake.helpers.orderedset import OrderedSet
from lemoncheesecake.helpers.introspection import get_callable_args, get_object_attributes
from lemoncheesecake.testtree import BaseTest, BaseSuite, flatten_tests_as_dict

SUITE_HOOKS = "setup_test", "teardown_test", "setup_suite", "teardown_suite"


def _is_node_disabled(node):
    while node is not None:
        if node.disabled:
            return node.disabled
        node = node.parent_suite
    return False


class Test(BaseTest):
    """
    Internal representation of a test.
    """
    def __init__(self, name, description, callback):
        BaseTest.__init__(self, name, description)
        self.callback = callback
        self.disabled = False
        self.hidden = False
        self.rank = 0
        self.dependencies = []
        self.resolved_dependencies = []
        self.parameters = {}

    def is_disabled(self):
        return _is_node_disabled(self)

    def is_enabled(self):
        return not self.is_disabled()

    def get_arguments(self):
        return get_callable_args(self.callback)

    def get_fixtures(self):
        return list(filter(lambda arg: arg not in self.parameters, self.get_arguments()))


class InjectedFixture:
    def __init__(self, fixture_name):
        self.fixture_name = fixture_name


class Suite(BaseSuite):
    """
    Internal representation of a suite.
    """
    def __init__(self, obj, name, description):
        BaseSuite.__init__(self, name, description)
        self.obj = obj
        self.rank = 0
        self.disabled = False
        self.hidden = False
        self._hooks = {}
        self._injected_fixtures = self._load_injected_fixtures(obj) if obj else {}
        # to optimize unique constraint checks on test/suite name/description, keep those
        # strings in sets:
        self._test_names = set()
        self._test_descriptions = set()
        self._sub_suite_names = set()
        self._sub_suite_descriptions = set()

    @staticmethod
    def _assert_hook_name(hook_name):
        assert hook_name in SUITE_HOOKS, "Invalid hook name '%s'" % hook_name

    @staticmethod
    def _load_injected_fixtures(obj):
        fixtures = {}
        for attr_name, attr in get_object_attributes(obj):
            if isinstance(attr, InjectedFixture):
                fixtures[attr.fixture_name or attr_name] = attr_name
        return fixtures

    def is_disabled(self):
        return _is_node_disabled(self)

    def has_enabled_tests(self):
        return any(test.is_enabled() for test in self.get_tests())

    def add_hook(self, hook_name, func):
        self._assert_hook_name(hook_name)
        self._hooks[hook_name] = func

    def has_hook(self, hook_name):
        self._assert_hook_name(hook_name)
        return hook_name in self._hooks

    def get_hook(self, hook_name):
        self._assert_hook_name(hook_name)
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

    def add_test(self, test):
        if test.description in self._test_descriptions:
            raise SuiteLoadingError(
                "A test with description '%s' is already registered in test suite %s" % (test.description, self.path)
            )
        if test.name in self._test_names:
            raise SuiteLoadingError(
                "A test with name '%s' is already registered in test suite %s" % (test.name, self.path)
            )

        BaseSuite.add_test(self, test)
        self._test_names.add(test.name)
        self._test_descriptions.add(test.description)

    def add_suite(self, suite):
        if suite.description in self._sub_suite_descriptions:
            raise SuiteLoadingError(
                "A sub test suite with description '%s' is already registered in test suite %s" % (suite.name, self.path)
            )
        if suite.name in self._sub_suite_names:
            raise SuiteLoadingError(
                "A sub test suite with name '%s' is already registered in test suite %s" % (suite.name, self.path)
            )

        BaseSuite.add_suite(self, suite)
        self._sub_suite_names.add(suite.name)
        self._sub_suite_descriptions.add(suite.description)

    def pull_node(self):
        suite = BaseSuite.pull_node(self)
        suite._test_names = set()
        suite._test_descriptions = set()
        suite._sub_suite_names = set()
        suite._sub_suite_descriptions = set()
        return suite

    def get_fixtures(self):
        fixtures = OrderedSet(self._injected_fixtures.keys())

        suite_setup = self.get_hook("setup_suite")
        if suite_setup:
            fixtures.update(get_callable_args(suite_setup))

        return fixtures


def _normalize_test_dependencies(test: Test, all_tests: Dict[str, Test]):
    for test_dep in test.dependencies:
        if callable(test_dep):
            for other_test in all_tests.values():
                if other_test != test and test_dep(other_test):
                    yield other_test
        else:
            try:
                yield all_tests[test_dep]
            except KeyError:
                raise ValidationError(
                    f"Cannot find dependency test '{test_dep}' for '{test.path}'"
                )


def _resolve_test_dependencies(test: Test, scheduled_tests: Dict[str, Test], all_tests: Dict[str, Test],
                               ref_tests: Sequence[str] = ()):
    # NB: the all_tests vs scheduled_tests distinction is here to make sure that an existing test dependency
    # (i.e present in all_tests) is really going to be run (i.e present in scheduled_tests)
    ref_tests = [test.path] + list(ref_tests)
    resolved_dependencies = []

    for dep_test in _normalize_test_dependencies(test, all_tests):
        if dep_test.path in ref_tests:
            raise ValidationError(f"Got circular dependency on test {test.path} through test {dep_test.path}")
        if dep_test.path not in scheduled_tests:
            raise ValidationError(
                f"Error: test dependency '{dep_test.path}' of '{test.path}' "
                "is not going to be run"
            )

        resolved_dependencies.append(dep_test)
        _resolve_test_dependencies(dep_test, scheduled_tests, all_tests, ref_tests)

    return resolved_dependencies


def resolve_tests_dependencies(scheduled_suites: Iterable[Suite], all_suites: Iterable[Suite]):
    scheduled_tests = flatten_tests_as_dict(scheduled_suites)
    all_tests = flatten_tests_as_dict(all_suites)
    for test in scheduled_tests.values():
        test.resolved_dependencies = _resolve_test_dependencies(test, scheduled_tests, all_tests)
