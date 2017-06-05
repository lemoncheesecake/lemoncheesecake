'''
Created on Jan 7, 2017

@author: nicolas
'''

import inspect
import re

from lemoncheesecake.importer import import_module, get_matching_files, get_py_files_from_dir
from lemoncheesecake.exceptions import FixtureError, ImportFixtureError, ProgrammingError, \
    serialize_current_exception
from lemoncheesecake.utils import get_distincts_in_list, get_callable_args

__all__ = (
    "fixture",
    "load_fixtures_from_func", "load_fixtures_from_file",
    "load_fixtures_from_files", "load_fixtures_from_directory"
)

FORBIDDEN_FIXTURE_NAMES = ("fixture_name", )
SCOPE_LEVELS = {
    "test": 1,
    "testsuite": 2,
    "session": 3,
    "session_prerun": 4
}

class FixtureInfo:
    def __init__(self, names, scope):
        self.names = names
        self.scope = scope

def fixture(names=None, scope="test"):
    if scope not in ("test", "testsuite", "session", "session_prerun"):
        raise ProgrammingError("Invalid fixture scope '%s'" % scope)
    
    def wrapper(func):
        setattr(func, "_lccfixtureinfo", FixtureInfo(names, scope))
        return func
    
    return wrapper

class BaseFixture:
    def is_builtin(self):
        return False
    
    def get_scope_level(self):
        return {
            "test": 1,
            "testsuite": 2,
            "session": 3,
            "session_prerun": 4
        }[self.scope]

    def is_executed(self):
        return hasattr(self, "_result")

    def teardown(self):
        pass
    
    def reset(self):
        pass
    
class Fixture(BaseFixture):
    def __init__(self, name, func, scope, params):
        self.name = name
        self.func = func
        self.scope = scope
        self.params = params
        self._generator = None

    def execute(self, params={}):
        assert not self.is_executed(), "fixture '%s' has already been executed" % self.name
        for param_name in params.keys():
            assert param_name in self.params

        result = self.func(**params)
        if inspect.isgenerator(result):
            self._generator = result
            self._result = next(result)
        else:
            self._result = result
    
    def get_result(self):
        assert self.is_executed(), "fixture '%s' has not been executed" % self.name
        return self._result
    
    def teardown(self):
        assert self.is_executed(), "fixture '%s' has not been executed" % self.name
        delattr(self, "_result")
        if self._generator:
            try:
                next(self._generator)
            except StopIteration:
                self._generator = None
            else:
                raise FixtureError("The fixture yields more than once, only one yield is supported") 
    
class BuiltinFixture(BaseFixture):
    def __init__(self, name, value):
        self.name = name
        self.scope = "session_prerun"
        self.params = []
        self._value = value
    
    def is_builtin(self):
        return True
        
    def execute(self, params={}):
        self._result = self._value() if callable(self._value) else self._value
    
    def get_result(self):
        return self._result

class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}
    
    def add_fixture(self, fixture):
        if fixture.name in self._fixtures and self._fixtures[fixture.name].is_builtin():
            raise FixtureError("'%s' is a builtin fixture name" % fixture.name)
        self._fixtures[fixture.name] = fixture
    
    def add_fixtures(self, fixtures):
        for fixture in fixtures:
            self.add_fixture(fixture)
    
    def get_fixture(self, name):
        return self._fixtures[name]
    
    def _get_fixture_dependencies(self, name, orig_fixture):
        fixture_params = [p for p in self._fixtures[name].params if p != "fixture_name"]
        if orig_fixture and orig_fixture in fixture_params:
            raise FixtureError("Fixture '%s' has a circular dependency on fixture '%s'" % (orig_fixture, name))

        dependencies = []
        for param in fixture_params:
            if param not in self._fixtures:
                raise FixtureError("Fixture '%s' used by fixture '%s' does not exist" % (param, name))
            dependencies.extend(self._get_fixture_dependencies(param, orig_fixture if orig_fixture else name)) 
        dependencies.extend(fixture_params)
        
        return dependencies
    
    def get_fixture_dependencies(self, name):
        dependencies = self._get_fixture_dependencies(name, None)
        return get_distincts_in_list(dependencies)
    
    def filter_fixtures(self, base_names=[], scope=None, is_executed=None, with_dependencies=False):
        def do_filter_fixture(fixture):
            if scope != None and fixture.scope != scope:
                return False
            if is_executed != None and fixture.is_executed() != is_executed:
                return False
            return True
        
        names = base_names if base_names else self._fixtures.keys()
        fixtures = filter(do_filter_fixture, [self._fixtures[name] for name in names])
        return [f.name for f in fixtures]
    
    def check_dependencies(self):
        """
        Checks for:
        - missing dependencies
        - circular dependencies
        - scope incoherence
        - forbidden fixture name
        raises FixtureError if a check fails
        """
        # first, check for forbidden fixture name
        for fixture_name in self._fixtures.keys():
            if fixture_name in FORBIDDEN_FIXTURE_NAMES:
                raise FixtureError("Fixture name '%s' is forbidden" % fixture_name)
        
        # second, check for missing & circular dependencies
        for fixture_name in self._fixtures.keys():
            self.get_fixture_dependencies(fixture_name)
        
        # third, check fixture scope compliance with their direct fixture dependencies
        for fixture in self._fixtures.values():
            dependency_fixtures = [self._fixtures[param] for param in fixture.params if param != "fixture_name"]
            for dependency_fixture in dependency_fixtures:
                if dependency_fixture.get_scope_level() < fixture.get_scope_level():
                    raise FixtureError("Fixture '%s' with scope '%s' is incompatible with scope '%s' of fixture '%s'" % (
                        fixture.name, fixture.scope, dependency_fixture.scope, dependency_fixture.name
                    ))
        
    
    def check_fixtures_in_test(self, test, suite):
        for fixture in test.get_params():
            if fixture not in self._fixtures:
                raise FixtureError("Unknown fixture '%s' used in test '%s'" % (fixture, test.get_path_str()))
        
    def check_fixtures_in_testsuite(self, suite):
        if suite.has_hook("setup_suite"):
            for fixture in suite.get_hook_params("setup_suite"):
                if fixture not in self._fixtures:
                    raise FixtureError("Unknown fixture '%s' used in setup_suite of suite '%s'" % (fixture, suite.get_path_str()))
                if self._fixtures[fixture].get_scope_level() < SCOPE_LEVELS["testsuite"]:
                    raise FixtureError("In suite '%s' setup_suite uses fixture '%s' which has an incompatible scope" % (
                        suite.get_path_str(), fixture
                    ))
        
        for test in suite.get_tests():
            self.check_fixtures_in_test(test, suite)
        
        for sub_suite in suite.get_sub_testsuites():
            self.check_fixtures_in_testsuite(sub_suite)
    
    def check_fixtures_in_testsuites(self, suites):
        for suite in suites:
            self.check_fixtures_in_testsuite(suite)

    def get_fixture_scope(self, name):
        return self._fixtures[name].scope
    
    def execute_fixture(self, name):
        fixture = self._fixtures[name]
        params = {}
        for param in fixture.params:
            if param == "fixture_name":
                params["fixture_name"] = name
            else:
                dependency_fixture = self._fixtures[param]
                if not dependency_fixture.is_executed():
                    self.execute_fixture(dependency_fixture.name)
                params[dependency_fixture.name] = dependency_fixture.get_result()
        fixture.execute(params)
        
    def get_fixture_result(self, name):
        return self._fixtures[name].get_result()
    
    def is_fixture_executed(self, name):
        return self._fixtures[name].is_executed()
    
    def get_fixture_results_as_params(self, names):
        results = {}
        for name in names:
            results[name] = self.get_fixture_result(name)
        return results
    
    def teardown_fixture(self, name):
        self._fixtures[name].teardown()

def load_fixtures_from_func(func):
    assert hasattr(func, "_lccfixtureinfo")
    names = func._lccfixtureinfo.names
    if not names:
        names = [func.__name__]
    scope = func._lccfixtureinfo.scope
    args = get_callable_args(func)
    return [Fixture(name, func, scope, args) for name in names]

def load_fixtures_from_file(filename):
    try:
        mod = import_module(filename)
    except ImportError:
        raise ImportFixtureError(
            "Cannot import file '%s': %s" % (filename, serialize_current_exception(show_stacktrace=True))
        )
    fixtures = []
    for sym_name in dir(mod):
        sym = getattr(mod, sym_name)
        if hasattr(sym, "_lccfixtureinfo"):
            fixtures.extend(load_fixtures_from_func(sym))
    return fixtures

def load_fixtures_from_files(patterns, excluding=[]):
    """
    Import fixtures from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: load_testsuites_from_files("test_*.py")
    """
    fixtures = []
    for file in get_matching_files(patterns, excluding):
        fixtures.extend(load_fixtures_from_file(file))
    return fixtures

def load_fixtures_from_directory(dir):
    fixtures = []
    for file in get_py_files_from_dir(dir):
        fixtures.extend(load_fixtures_from_file(file))
    return fixtures
