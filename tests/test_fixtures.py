import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.fixture import load_fixtures_from_func, FixtureRegistry, BuiltinFixture
from lemoncheesecake.suite import load_suite_from_class, load_suites_from_classes

from lemoncheesecake import exceptions

from helpers.runner import build_fixture_registry


def test_fixture_decorator():
    @lcc.fixture()
    def myfixture():
        pass

    assert myfixture._lccfixtureinfo
    assert myfixture._lccfixtureinfo.scope == "test"


def test_fixture_decorator_invalid_scope():
    with pytest.raises(ValueError, match=r"Invalid fixture scope"):
        @lcc.fixture(scope="not_a_valid_scope")
        def myfixt():
            pass


def test_fixture_decorator_invalid_per_thread():
    with pytest.raises(AssertionError, match=r"can only be per_thread"):
        @lcc.fixture(scope="test", per_thread=True)
        def myfixt():
            pass


def test_load_from_func():
    @lcc.fixture()
    def myfixture():
        pass

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert len(fixtures[0].params) == 0


def test_load_from_func_with_multiple_fixture_names():
    @lcc.fixture(names=["foo", "bar"])
    def myfixture():
        pass

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 2
    assert fixtures[0].name == "foo"
    assert fixtures[0].scope == "test"
    assert len(fixtures[0].params) == 0
    assert fixtures[1].name == "bar"
    assert fixtures[1].scope == "test"
    assert len(fixtures[1].params) == 0


def test_load_from_func_with_parameters():
    @lcc.fixture()
    def myfixture(foo, bar):
        pass

    fixtures = load_fixtures_from_func(myfixture)

    assert len(fixtures) == 1
    assert fixtures[0].name == "myfixture"
    assert fixtures[0].scope == "test"
    assert fixtures[0].params == ["foo", "bar"]


def test_execute_fixture():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({})
    assert result.get() == 42


def test_execute_fixture_builtin():
    fixture = BuiltinFixture("fix", 42)
    result = fixture.execute({})
    assert result.get() == 42


def test_execute_fixture_with_yield():
    @lcc.fixture()
    def myfixture():
        yield 42

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({})
    assert result.get() == 42


def test_teardown_fixture():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({})
    result.get()
    result.teardown()


def test_teardown_fixture_with_yield():
    flag = []
    @lcc.fixture()
    def myfixture():
        yield 42
        flag.append(True)

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({})
    assert result.get() == 42
    assert not flag
    result.teardown()
    assert flag


def test_execute_fixture_with_parameters():
    @lcc.fixture()
    def myfixture(val):
        return val * 2

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({"val": 3})
    assert result.get() == 6


def test_get_fixture_result_multiple_times():
    @lcc.fixture()
    def myfixture():
        return 42

    fixture = load_fixtures_from_func(myfixture)[0]
    result = fixture.execute({})
    assert result.get() == 42
    assert result.get() == 42
    assert result.get() == 42


def test_fixture_executed_multiple_times():
    @lcc.fixture()
    def myfixture(val):
        return val * 2

    fixture = load_fixtures_from_func(myfixture)[0]

    result = fixture.execute({"val": 3})
    assert result.get() == 6

    result = fixture.execute({"val": 4})
    assert result.get() == 8


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
    with pytest.raises(exceptions.LemoncheesecakeException) as excinfo:
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
    with pytest.raises(exceptions.LemoncheesecakeException) as excinfo:
        registry.get_fixture_dependencies("foo")
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
    with pytest.raises(exceptions.LemoncheesecakeException) as excinfo:
        registry.get_fixture_dependencies("foo")
    assert 'circular' in str(excinfo.value)


def test_registry_fixture_circular_dependency_indirect_2():
    @lcc.fixture()
    def baz(bar):
        return bar * 2

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

    with pytest.raises(exceptions.LemoncheesecakeException) as excinfo:
        registry.get_fixture_dependencies("foo")
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
    with pytest.raises(exceptions.LemoncheesecakeException) as excinfo:
        registry.check_dependencies()
    assert 'incompatible' in str(excinfo.value)


def test_registry_forbidden_fixture_name():
    @lcc.fixture(scope="test")
    def fixture_name():
        return 0

    registry = FixtureRegistry()
    registry.add_fixtures(load_fixtures_from_func(fixture_name))
    with pytest.raises(exceptions.ValidationError) as excinfo:
        registry.check_dependencies()
    assert "forbidden" in str(excinfo.value)


def build_registry():
    @lcc.fixture(scope="pre_run")
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

    return registry


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
    with pytest.raises(exceptions.ValidationError):
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
    with pytest.raises(exceptions.ValidationError):
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
    with pytest.raises(exceptions.ValidationError):
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
    with pytest.raises(exceptions.ValidationError):
        registry.check_fixtures_in_suites([suite])


def test_check_fixture_in_suites_parametrized_test():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized([{"value": 1}])
        def sometest(self, value):
            pass

    suite = load_suite_from_class(MySuite)
    registry = build_registry()
    registry.check_fixtures_in_suites([suite])


def test_check_fixture_in_suite_incompatible_dependency_on_per_thread_fixture():
    @lcc.fixture(scope="session", per_thread=True)
    def fixt():
        pass

    @lcc.suite()
    class Suite:
        def setup_suite(self, fixt):
            pass

    suite = load_suite_from_class(Suite)
    registry = build_fixture_registry(fixt)
    with pytest.raises(exceptions.ValidationError, match=r"per-thread.+not allowed"):
        registry.check_fixtures_in_suite(suite)


def test_check_fixture_dependencies_incompatible_dependency_on_per_thread_fixture():
    @lcc.fixture(scope="session", per_thread=True)
    def per_thread_fixture():
        pass

    @lcc.fixture(scope="suite")
    def suite_fixture(per_thread_fixture):
        pass

    registry = build_fixture_registry(per_thread_fixture, suite_fixture)
    with pytest.raises(exceptions.ValidationError, match=r"incompatible with per-thread fixture"):
        registry.check_dependencies()


@pytest.fixture()
def fixture_registry_sample():
    @lcc.fixture(scope="pre_run")
    def fixt_for_pre_run1():
        pass

    @lcc.fixture(scope="session")
    def fixt_for_session1():
        pass

    @lcc.fixture(scope="session")
    def fixt_for_session2(fixt_for_pre_run1):
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
        fixt_for_pre_run1, fixt_for_session1, fixt_for_session2, fixt_for_session3,
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


def test_get_fixtures_scheduled_for_pre_run(fixture_registry_sample, suites_sample):
    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_pre_run(suites_sample)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_pre_run1"]


def test_get_fixtures_scheduled_for_session(fixture_registry_sample, suites_sample):
    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_session(suites_sample, None)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_session1", "fixt_for_session2"]


def test_get_fixtures_scheduled_for_suite(fixture_registry_sample, suites_sample):
    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_suite(suites_sample[0], None)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_suite1"]

    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_suite(suites_sample[1], None)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_suite1"]


def test_get_fixtures_scheduled_for_test(fixture_registry_sample, suites_sample):
    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[0].get_tests()[0], None)
    assert sorted(scheduled.get_fixture_names()) == []

    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[0].get_tests()[1], None)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_test3"]

    scheduled = fixture_registry_sample.get_fixtures_scheduled_for_test(suites_sample[1].get_tests()[0], None)
    assert sorted(scheduled.get_fixture_names()) == ["fixt_for_test1", "fixt_for_test2"]
