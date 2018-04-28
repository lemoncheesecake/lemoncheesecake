import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.fixtures import load_fixtures_from_func, FixtureRegistry, BuiltinFixture
from lemoncheesecake.suite import load_suite_from_class, load_suites_from_classes

from lemoncheesecake import exceptions

from helpers.runner import build_fixture_registry


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

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() is False
    assert len(fixtures[0].params) == 0


def test_load_from_func_with_multiple_fixture_names():
    @lcc.fixture(names=["foo", "bar"])
    def myfixture():
        pass

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 2
    assert fixtures[0].name == "foo"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() is False
    assert len(fixtures[0].params) == 0
    assert fixtures[1].name == "bar"
    assert fixtures[1].scope == "test"
    assert fixtures[1].is_executed() is False
    assert len(fixtures[1].params) == 0


def test_load_from_func_with_parameters():
    @lcc.fixture()
    def myfixture(foo, bar):
        pass

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert fixtures[0].is_executed() is False
    assert fixtures[0].params == ["foo", "bar"]


def test_execute_fixture():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42


def test_execute_fixture_builtin():
    fixture = BuiltinFixture("fix", 42)
    fixture.execute()
    assert fixture.get_result() == 42


def test_execute_fixture_builtin_lambda():
    fixture = BuiltinFixture("fix", lambda: 42)
    fixture.execute()
    assert fixture.get_result() == 42


def test_execute_fixture_with_yield():
    @lcc.fixture()
    def myfixture():
        yield 42

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42


def test_teardown_fixture():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    fixture.get_result()
    fixture.teardown()


def test_teardown_fixture_with_yield():
    flag = []
    @lcc.fixture()
    def myfixture():
        yield 42
        flag.append(True)

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42
    assert not flag
    fixture.teardown()
    assert flag


def test_execute_fixture_with_parameters():
    @lcc.fixture()
    def myfixture(val):
        return val * 2

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute({"val": 3})
    assert fixture.get_result() == 6


def test_get_fixture_result_multiple_times():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    fixture.execute()
    assert fixture.get_result() == 42
    assert fixture.get_result() == 42
    assert fixture.get_result() == 42


def test_reset_fixture():
    @lcc.fixture()
    def myfixture(val):
        return val * 2

    fixture = load_fixtures_from_func(myfixture)[0]

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
    registry.add_fixtures(load_fixtures_from_func(myfixture))
    registry.check_dependencies()


def test_registry_fixture_with_params():
    @lcc.fixture()
    def foo():
        return 21

    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    registry.check_dependencies()


def test_registry_fixture_missing_dependency():
    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(bar))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert "does not exist" in str(excinfo.value)


def test_registry_fixture_circular_dependency_direct():
    @lcc.fixture()
    def foo(bar):
        return bar * 2

    @lcc.fixture()
    def bar(foo):
        return foo * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
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
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    registry.add_fixtures(load_fixtures_from_func(baz))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'circular' in str(excinfo.value)


def test_registry_fixture_name():
    @lcc.fixture()
    def foo(fixture_name):
        pass

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.check_dependencies()


def test_registry_get_fixture_without_param_dependency():
    @lcc.fixture()
    def foo():
        return 42

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    assert registry.get_fixture_dependencies("foo") == []


def test_registry_get_fixture_with_param_dependency():
    @lcc.fixture()
    def bar():
        return 21

    @lcc.fixture()
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
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
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    registry.add_fixtures(load_fixtures_from_func(baz))
    registry.add_fixtures(load_fixtures_from_func(zoub))
    assert registry.get_fixture_dependencies("foo") == ["zoub", "baz", "bar"]


def test_registry_compatible_scope():
    @lcc.fixture(scope="session")
    def bar():
        return 21

    @lcc.fixture(scope="test")
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    registry.check_dependencies()


def test_registry_incompatible_scope():
    @lcc.fixture(scope="test")
    def bar():
        return 21

    @lcc.fixture(scope="session")
    def foo(bar):
        return bar * 2

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    with pytest.raises(exceptions.LemonCheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'incompatible' in str(excinfo.value)


def test_registry_forbidden_fixture_name():
    @lcc.fixture(scope="test")
    def fixture_name():
        return 0

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(fixture_name))
    with pytest.raises(exceptions.FixtureError) as excinfo:
        registry.check_dependencies()
    assert "forbidden" in str(excinfo.value)


def test_registry_execute_fixture_without_dependency():
    @lcc.fixture()
    def foo():
        return 42

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(foo))
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
    registry.add_fixtures(load_fixtures_from_func(foo))
    registry.add_fixtures(load_fixtures_from_func(bar))
    registry.execute_fixture("foo")
    assert registry.get_fixture_result("foo") == 42


def build_registry(*executed_fixtures):
    @lcc.fixture(scope="session_prerun")
    def fix0():
        pass

    @lcc.fixture(scope="session")
    def fix1():
        pass

    @lcc.fixture(scope="suite")
    def fix2():
        pass

    @lcc.fixture(scope="test")
    def fix3():
        pass

    @lcc.fixture(names=["fix4", "fix5"])
    def fix_():
        pass

    registry = FixtureRegistry()
    for func in fix0, fix1, fix2, fix3, fix_:
        registry.add_fixtures(load_fixtures_from_func(func))

    for fixture_name in executed_fixtures:
        registry.execute_fixture(fixture_name)

    return registry


def test_filter_fixtures_all():
    assert sorted(build_registry().filter_fixtures()) == ["fix0", "fix1", "fix2", "fix3", "fix4", "fix5"]


def test_filter_fixtures_on_scope():
    assert sorted(build_registry().filter_fixtures(scope="suite")) == ["fix2"]


def test_filter_fixtures_on_executed():
    registry = build_registry("fix3", "fix4")
    assert sorted(registry.filter_fixtures(is_executed=True)) == ["fix3", "fix4"]
    assert sorted(registry.filter_fixtures(is_executed=False)) == ["fix0", "fix1", "fix2", "fix5"]


def test_filter_fixtures_on_base_names():
    assert sorted(build_registry().filter_fixtures(base_names=["fix1"])) == ["fix1"]


def test_filter_fixtures_on_all_criteria():
    registry = build_registry("fix5")
    fixtures = registry.filter_fixtures(base_names=["fix5"], is_executed=True, scope="test")
    assert sorted(fixtures) == ["fix5"]


def test_check_fixtures_in_suites_ok():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.test("test")
            def sometest(self, fix1):
                pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    registry.check_fixtures_in_suites([suite])


def test_check_fixtures_in_suites_unknown_fixture_in_test():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.test("test")
            def sometest(self, unknown_fix):
                pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    with pytest.raises(exceptions.FixtureError):
        registry.check_fixtures_in_suites([suite])


def test_check_fixtures_in_suites_unknown_fixture_in_setup_suite():
    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self, unknown_fix):
            pass

        @lcc.test("test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    with pytest.raises(exceptions.FixtureError):
        registry.check_fixtures_in_suites([suite])


def test_check_fixtures_in_suites_incompatible_fixture_in_setup_suite():
    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self, fix3):
            pass

        @lcc.test("test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    with pytest.raises(exceptions.FixtureError):
        registry.check_fixtures_in_suites([suite])


def test_check_fixtures_in_suites_incompatible_fixture_in_inject():
    @lcc.suite("MySuite")
    class MySuite:
        fix3 = lcc.inject_fixture()

        @lcc.test("test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    with pytest.raises(exceptions.FixtureError):
        registry.check_fixtures_in_suites([suite])


@pytest.fixture()
def fixture_registry_sample():
    @lcc.fixture(scope="session_prerun")
    def fixt_for_session_prerun1():
        pass

    @lcc.fixture(scope="session")
    def fixt_for_session1():
        pass

    @lcc.fixture(scope="session")
    def fixt_for_session2(fixt_for_session_prerun1):
        pass

    @lcc.fixture(scope="session")
    def fixt_for_session3():
        pass

    @lcc.fixture(scope="suite")
    def fixt_for_suite1(fixt_for_session1):
        pass

    @lcc.fixture(scope="suite")
    def fixt_for_suite2(fixt_for_session2):
        pass

    @lcc.fixture(scope="test")
    def fixt_for_test1(fixt_for_suite1):
        pass

    @lcc.fixture(scope="test")
    def fixt_for_test2(fixt_for_test1):
        pass

    @lcc.fixture(scope="test")
    def fixt_for_test3(fixt_for_session2):
        pass

    return build_fixture_registry(
        fixt_for_session_prerun1, fixt_for_session1, fixt_for_session2, fixt_for_session3,
        fixt_for_suite1, fixt_for_suite2,
        fixt_for_test1, fixt_for_test2, fixt_for_test3
    )


@pytest.fixture()
def suites_sample():
    @lcc.suite("suite1")
    class suite1:
        @lcc.test("Test 1")
        def suite1_test1(self, fixt_for_suite1):
            pass

        @lcc.test("Test 2")
        def suite1_test2(self, fixt_for_test3):
            pass

    @lcc.suite("suite2")
    class suite2:
        @lcc.test("Test 1")
        def suite2_test1(self, fixt_for_test2):
            pass

    return load_suites_from_classes([suite1, suite2])


def test_get_fixtures_scheduled_for_session_prerun(fixture_registry_sample, suites_sample):
    actual = fixture_registry_sample.get_fixtures_scheduled_for_session_prerun(suites_sample)
    assert sorted(actual) == ["fixt_for_session_prerun1"]


def test_get_fixtures_scheduled_for_session(fixture_registry_sample, suites_sample):
    actual = fixture_registry_sample.get_fixtures_scheduled_for_session(suites_sample)
    assert sorted(actual) == ["fixt_for_session1", "fixt_for_session2"]


def test_get_fixtures_scheduled_for_suite(fixture_registry_sample, suites_sample):
    assert sorted(fixture_registry_sample.get_fixtures_scheduled_for_suite(suites_sample[0])) == ["fixt_for_suite1"]
    assert sorted(fixture_registry_sample.get_fixtures_scheduled_for_suite(suites_sample[1])) == ["fixt_for_suite1"]


def test_get_fixtures_scheduled_for_test(fixture_registry_sample, suites_sample):
    assert sorted(fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[0].get_tests()[0])) == []
    assert sorted(fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[0].get_tests()[1])) == ["fixt_for_test3"]
    assert sorted(fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[1].get_tests()[0])) == ["fixt_for_test1", "fixt_for_test2"]
