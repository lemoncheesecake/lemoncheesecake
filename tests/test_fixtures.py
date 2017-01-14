import sys

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.fixtures import FixtureRegistry
from lemoncheesecake import exceptions

def test_fixture_decorator():
    @lcc.fixture()
    def myfixture():
        pass
    
    assert myfixture._lccfixtureinfo
    assert myfixture._lccfixtureinfo.scope == "test"

def test_load_from_func():
    @lcc.fixture()
    def myfixture():
        pass
    
    fixtures = lcc.load_fixtures_from_func(myfixture)
    
    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() == False
    assert len(fixtures[0].params) == 0

def test_load_from_func_with_multiple_fixture_names():
    @lcc.fixture(names=["foo", "bar"])
    def myfixture():
        pass
    
    fixtures = lcc.load_fixtures_from_func(myfixture)
    
    assert len(fixtures) == 2
    assert fixtures[0].name == "foo"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() == False
    assert len(fixtures[0].params) == 0
    assert fixtures[1].name == "bar"
    assert fixtures[1].scope == "test"
    assert fixtures[1].is_executed() == False
    assert len(fixtures[1].params) == 0

def test_load_from_func_with_parameters():
    @lcc.fixture()
    def myfixture(foo, bar):
        pass
    
    fixtures = lcc.load_fixtures_from_func(myfixture)
    
    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() == False
    assert fixtures[0].params == ["foo", "bar"]

def test_execute_fixture():
    @lcc.fixture()
    def myfixture():
        return 42
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42

def test_execute_fixture_with_yield():
    @lcc.fixture()
    def myfixture():
        yield 42    
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42

def test_teardown_fixture():
    @lcc.fixture()
    def myfixture():
        return 42
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    fixture.get_result()
    fixture.teardown()

def test_teardown_fixture_with_yield():
    flag = []
    @lcc.fixture()
    def myfixture():
        yield 42
        flag.append(True)
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42
    assert not flag
    fixture.teardown()
    assert flag

def test_execute_fixture_with_parameters():
    @lcc.fixture()
    def myfixture(val):
        return val * 2
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute({"val": 3})
    assert fixture.get_result() == 6

def test_get_fixture_result_multiple_times():
    @lcc.fixture()
    def myfixture():
        return 42
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42
    assert fixture.get_result() == 42
    assert fixture.get_result() == 42

def test_reset_fixture():
    @lcc.fixture()
    def myfixture(val):
        return val * 2
    
    fixture = lcc.load_fixtures_from_func(myfixture)[0]
    
    fixture.execute({"val": 3})
    assert fixture.get_result() == 6
    fixture.teardown()
    fixture.reset()
    
    fixture.execute({"val": 4})
    assert fixture.get_result() == 8

def test_registry_fixture_without_params():
    @lcc.fixture()
    def myfixture():
        return 42

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(myfixture))
    registry.check_dependencies()

def test_registry_fixture_with_params():
    @lcc.fixture()
    def foo():
        return 21

    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    registry.check_dependencies()

def test_registry_fixture_missing_dependency():
    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'Unknown' in str(excinfo.value)

def test_registry_fixture_circular_dependency_direct():
    @lcc.fixture()
    def foo(bar):
        return bar * 2

    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'circular' in str(excinfo.value)

def test_registry_fixture_circular_dependency_indirect():
    @lcc.fixture()
    def baz(foo):
        return foo * 2

    @lcc.fixture()
    def bar(baz):
        return baz * 2

    @lcc.fixture()
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    registry.add_fixtures(lcc.load_fixtures_from_func(baz))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'circular' in str(excinfo.value)

def test_registry_get_fixture_without_param_dependency():
    @lcc.fixture()
    def foo():
        return 42

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    assert registry.get_fixture_dependencies("foo") == []

def test_registry_get_fixture_with_param_dependency():
    @lcc.fixture()
    def bar():
        return 21
    
    @lcc.fixture()
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    assert registry.get_fixture_dependencies("foo") == ["bar"]

def test_registry_get_fixture_with_params_dependency():
    @lcc.fixture()
    def zoub():
        return 21

    @lcc.fixture()
    def baz(zoub):
        return zoub

    @lcc.fixture()
    def bar(baz):
        return baz * 2
    
    @lcc.fixture()
    def foo(bar, baz):
        return bar * baz

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    registry.add_fixtures(lcc.load_fixtures_from_func(baz))
    registry.add_fixtures(lcc.load_fixtures_from_func(zoub))
    assert registry.get_fixture_dependencies("foo") == ["zoub", "baz", "bar"]

def test_registry_compatible_scope():
    @lcc.fixture(scope="session")
    def bar():
        return 21
    
    @lcc.fixture(scope="test")
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    registry.check_dependencies()

def test_registry_incompatible_scope():
    @lcc.fixture(scope="test")
    def bar():
        return 21
    
    @lcc.fixture(scope="session")
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'incompatible' in str(excinfo.value)

def test_registry_execute_fixture_without_dependency():
    @lcc.fixture()
    def foo():
        return 42

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.execute_fixture("foo")
    assert registry.get_fixture_result("foo") == 42

def test_registry_execute_fixture_with_dependency():
    @lcc.fixture()
    def bar():
        return 21
    
    @lcc.fixture()
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(lcc.load_fixtures_from_func(foo))
    registry.add_fixtures(lcc.load_fixtures_from_func(bar))
    registry.execute_fixture("foo")
    assert registry.get_fixture_result("foo") == 42

def build_registry(*executed_fixtures):
    @lcc.fixture(scope="session")
    def fix1():
        pass
    
    @lcc.fixture(scope="testsuite")
    def fix2():
        pass
    
    @lcc.fixture(scope="test")
    def fix3():
        pass
    
    @lcc.fixture(names=["fix4", "fix5"])
    def fix_():
        pass

    registry = FixtureRegistry()
    for func in fix1, fix2, fix3, fix_:
        registry.add_fixtures(lcc.load_fixtures_from_func(func))
    
    for fixture_name in executed_fixtures:
        registry.execute_fixture(fixture_name)
    
    return registry

def test_filter_fixtures_all():
    assert sorted(build_registry().filter_fixtures()) == ["fix1", "fix2", "fix3", "fix4", "fix5"]
    
def test_filter_fixtures_on_scope():
    assert sorted(build_registry().filter_fixtures(scope="testsuite")) == ["fix2"]

def test_filter_fixtures_on_executed():
    registry = build_registry("fix3", "fix4")
    assert sorted(registry.filter_fixtures(is_executed=True)) == ["fix3", "fix4"]
    assert sorted(registry.filter_fixtures(is_executed=False)) == ["fix1", "fix2", "fix5"]

def test_filter_fixtures_on_base_names():
    assert sorted(build_registry().filter_fixtures(base_names=["fix1"])) == ["fix1"]

def test_filter_fixtures_on_all_criteria():
    registry = build_registry("fix5")
    fixtures = registry.filter_fixtures(base_names=["fix5"], is_executed=True, scope="test")
    assert sorted(fixtures) == ["fix5"]
