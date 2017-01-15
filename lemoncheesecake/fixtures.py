'''
Created on Jan 7, 2017

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import ProgrammingError, LemonCheesecakeException
from lemoncheesecake.utils import get_distincts_in_list

__all__ = ("fixture", "load_fixtures_from_func")

class FixtureInfo:
    def __init__(self, names, scope):
        self.names = names
        self.scope = scope

def fixture(names=None, scope="test"):
    if scope not in ("test", "testsuite", "session"):
        raise ValueError("Invalid fixture scope '%s'" % scope)
    
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
            "session": 3
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
        assert not self.is_executed()
        for param_name in params.keys():
            assert param_name in self.params

        result = self.func(**params)
        if inspect.isgenerator(result):
            self._generator = result
            self._result = next(result)
        else:
            self._result = result
    
    def get_result(self):
        assert self.is_executed()
        return self._result
    
    def teardown(self):
        assert self.is_executed()
        if self._generator:
            try:
                next(self._generator)
            except StopIteration:
                pass
            else:
                raise ProgrammingError("The fixture yields more than once, only one yield is supported") 
    
    def reset(self):
        assert self.is_executed()
        delattr(self, "_result")
        self._generator = None

class BuiltinFixture(BaseFixture):
    def __init__(self, name, value):
        self.name = name
        self.scope = "session"
        self.params = []
        self._value = value
    
    def is_builtin(self):
        return True
        
    def execute(self, params={}):
        self._result = self._value() if callable(self._value) else self._value
    
    def get_result(self):
        return self._result

def load_fixtures_from_func(func):
    assert hasattr(func, "_lccfixtureinfo")
    names = func._lccfixtureinfo.names
    if not names:
        names = [func.__name__]
    scope = func._lccfixtureinfo.scope
    params = inspect.getargspec(func).args
    return [Fixture(name, func, scope, params) for name in names]

class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}
    
    def add_fixture(self, fixture):
        if fixture.name in self._fixtures and self._fixtures[fixture.name].is_builtin():
            raise ProgrammingError("'%s' is a builtin fixture name" % fixture.name)
        self._fixtures[fixture.name] = fixture
    
    def add_fixtures(self, fixtures):
        for fixture in fixtures:
            self.add_fixture(fixture)
    
    def get_fixture(self, name):
        return self._fixtures[name]
    
    def _get_fixture_dependencies(self, name, orig_fixture):
        try:
            fixture_params = self._fixtures[name].params
        except KeyError:
            raise LemonCheesecakeException("Unknown fixture '%s'" % name)
            
        if orig_fixture and orig_fixture in fixture_params:
            raise LemonCheesecakeException("Fixture '%s' has a circular dependency on fixture '%s'" % (orig_fixture, name))

        dependencies = []
        for param in fixture_params:
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
        raises a LemoncheesecakeException if a check fails
        """
        # first, check for missing & circular dependencies
        for fixture_name in self._fixtures.keys():
            self.get_fixture_dependencies(fixture_name)
        
        # second, check fixture scope compliance with their direct fixture dependencies
        for fixture in self._fixtures.values():
            dependency_fixtures = [self._fixtures[param] for param in fixture.params]
            for dependency_fixture in dependency_fixtures:
                if dependency_fixture.get_scope_level() < fixture.get_scope_level():
                    raise LemonCheesecakeException("Fixture '%s' with scope '%s' is incompatible with scope '%s' of fixture '%s'" % (
                        fixture.name, fixture.scope, dependency_fixture.scope, dependency_fixture.name
                    ))

    def get_fixture_scope(self, name):
        return self._fixtures[name].scope
    
    def execute_fixture(self, name):
        fixture = self._fixtures[name]
        params = {}
        for param in fixture.params:
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