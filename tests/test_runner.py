'''
Created on Sep 30, 2016

@author: nicolas
'''
import threading
import time
from collections import defaultdict

import pytest

from lemoncheesecake.exceptions import *
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.suite import add_test_into_suite
from lemoncheesecake.reporting.report import ReportLocation
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.suite import load_suites_from_directory

from helpers.runner import run_suite_class, run_suite_classes, run_suites, run_suite, build_suite_from_module
from helpers.report import assert_test_statuses, assert_test_passed, assert_test_failed, assert_test_skipped, \
    assert_report_node_success, get_last_test, get_last_log


def test_test_success():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    assert_test_passed(run_suite_class(MySuite))


def test_test_failure():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            check_that("val", 1, equal_to(2))

    assert_test_failed(run_suite_class(MySuite))


def test_test_module():
    suite = build_suite_from_module("""
@lcc.test("Some test")
def sometest():
    pass
""")

    report = run_suite(suite)
    assert_test_passed(report)


def test_exception_unexpected():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("First test")
        def first_test(self):
            1 / 0

        @lcc.test("Second test")
        def second_test(self):
            pass

    assert_test_statuses(run_suite_class(MySuite), failed=["MySuite.first_test"], passed=["MySuite.second_test"])


def test_exception_aborttest():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            raise lcc.AbortTest("test error")

        @lcc.test("Some other test")
        def someothertest(self):
            pass

    assert_test_statuses(run_suite_class(MySuite), failed=["MySuite.sometest"], passed=["MySuite.someothertest"])


def test_exception_abortsuite():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MyFirstSuite")
        class MyFirstSuite:
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortSuite("test error")

            @lcc.test("Some other test")
            def someothertest(self):
                pass

        @lcc.suite("MySecondSuite")
        class MySecondSuite:
            @lcc.test("Another test")
            def anothertest(self):
                pass

    assert_test_statuses(
        run_suite_class(MySuite),
        failed=["MySuite.MyFirstSuite.sometest"],
        skipped=["MySuite.MyFirstSuite.someothertest"],
        passed=["MySuite.MySecondSuite.anothertest"],
    )


def test_exception_abortalltests():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MyFirstSuite")
        class MyFirstSuite:
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortAllTests("test error")

            @lcc.test("Some other test")
            def someothertest(self):
                pass

        @lcc.suite("MySecondSuite")
        class MySecondSuite:
            @lcc.test("Another test")
            def anothertest(self):
                pass

    assert_test_statuses(
        run_suite_class(MySuite),
        failed=["MySuite.MyFirstSuite.sometest"],
        skipped=["MySuite.MyFirstSuite.someothertest", "MySuite.MySecondSuite.anothertest"]
    )


def test_generated_test():
    @lcc.suite("MySuite")
    class MySuite:
        def __init__(self):
            def test_func():
                lcc.log_info("somelog")
            test = lcc.Test("mytest", "My Test", test_func)
            add_test_into_suite(test, self)

    assert_test_passed(run_suite_class(MySuite))


def test_sub_suite_inline():
    @lcc.suite("MyParentSuite")
    class MyParentSuite:
        @lcc.suite("MyChildSuite")
        class MyChildSuite:
            @lcc.test("Some test")
            def sometest(self):
                pass

    assert_test_passed(run_suite_class(MyParentSuite))


def test_sub_suite_with_dir_only(tmpdir):
    tmpdir.mkdir("parent_suite")
    tmpdir.join("parent_suite").join("child_suite.py").write("""
import lemoncheesecake.api as lcc

@lcc.test()
def my_test():
    lcc.log_info("some thing")
""")

    suites = load_suites_from_directory(tmpdir.strpath)
    report = run_suites(suites)

    assert_test_statuses(report, passed=("parent_suite.child_suite.my_test",))


def test_setup_test():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_test(self, test):
            marker.append(test.name)

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(MySuite)

    assert marker == ["sometest"]


def test_teardown_test():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def teardown_test(self, test, status):
            marker.append((test.name, status))

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(MySuite)

    assert marker[0] == ("sometest", "passed")


def test_teardown_test_after_test_failure():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def teardown_test(self, test, status):
            marker.append((test.name, status))

        @lcc.test("Some test")
        def sometest(self):
            1 / 0

    run_suite_class(MySuite)

    assert marker[0] == ("sometest", "failed")


def test_setup_suite():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            marker.append("ok")

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(MySuite)

    assert marker


def test_setup_suite_with_disabled_test():
    marker = []

    @lcc.suite("suite_1")
    class suite_1:
        def setup_suite(self):
            marker.append("ok")

        @lcc.test("test")
        @lcc.disabled()
        def test(self):
            pass

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2))

    assert_test_statuses(report, disabled=["suite_1.test"], passed=["suite_2.test"])

    assert not marker


def test_setup_suite_with_disabled_test_and_force_disabled():
    marker = []

    @lcc.suite("suite_1")
    class suite_1:
        def setup_suite(self):
            marker.append("ok")

        @lcc.test("test")
        @lcc.disabled()
        def test(self):
            pass

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2), force_disabled=True)

    assert_test_statuses(report, passed=["suite_1.test", "suite_2.test"])

    assert marker


def test_teardown_suite():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def teardown_suite(self):
            marker.append("ok")

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(MySuite)

    assert marker


def test_teardown_suite_with_disabled_test():
    marker = []

    @lcc.suite("suite_1")
    class suite_1:
        @lcc.test("test")
        @lcc.disabled()
        def test(self):
            pass

        def teardown_suite(self):
            marker.append("ok")

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2))

    assert_test_statuses(report, disabled=["suite_1.test"], passed=["suite_2.test"])

    assert not marker


def test_teardown_suite_with_disabled_test_and_force_disabled():
    marker = []

    @lcc.suite("suite_1")
    class suite_1:
        @lcc.test("test")
        @lcc.disabled()
        def test(self):
            pass

        def teardown_suite(self):
            marker.append("ok")

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2), force_disabled=True)

    assert_test_statuses(report, passed=["suite_1.test", "suite_2.test"])

    assert marker


def test_teardown_suite_after_test_failure():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def teardown_suite(self):
            marker.append("ok")

        @lcc.test("Some test")
        def sometest(self):
            1 / 0

    run_suite_class(MySuite)

    assert marker


def test_teardown_suite_after_test_failure_and_test_success():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def teardown_suite(self):
            marker.append("teardown_suite")

        @lcc.test("Test 1")
        def test_1(self):
            marker.append("test_1")
            1 / 0

        @lcc.test("Test 2")
        def test_2(self):
            marker.append("test_2")

    run_suite_class(MySuite)

    assert marker == ["test_1", "test_2", "teardown_suite"]


def test_setup_test_error():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_test(self, test):
            1 / 0

        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_test(self, test, status):
            marker.append(test)

    report = run_suite_class(MySuite)

    assert_test_failed(report)
    assert len(marker) == 0


def test_setup_test_error_in_fixture():
    @lcc.fixture()
    def fix():
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    assert_test_failed(run_suite_class(MySuite, fixtures=[fix]))


def test_teardown_test_error():
    @lcc.suite("MySuite")
    class MySuite:
        def teardown_test(self, test, status):
            1 / 0

        @lcc.test("Some test")
        def sometest(self):
            pass

    assert_test_failed(run_suite_class(MySuite))


def test_teardown_test_error_in_fixture():
    @lcc.fixture()
    def fix():
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    assert_test_failed(run_suite_class(MySuite, fixtures=[fix]))


def test_setup_suite_error_and_subsuite():
    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            1 / 0

        @lcc.test("test")
        def test(self):
            pass

        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.test("test")
            def test(self):
                pass

    assert_test_statuses(run_suite_class(MySuite), skipped=["MySuite.test"], passed=["MySuite.MySubSuite.test"])


def test_setup_suite_error_because_of_exception():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            1 / 0

        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            marker.append("suite_teardown")

    report = run_suite_class(MySuite)

    assert_test_skipped(report)
    assert not marker


def test_setup_suite_error_because_of_error_log():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_error("some error")

        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            marker.append("teardown")

    report = run_suite_class(MySuite)

    assert_test_skipped(report)
    assert not marker


def test_setup_suite_error_because_of_fixture():
    marker = []

    @lcc.fixture(scope="suite")
    def fix():
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

        @lcc.test("Some other test")
        def sometest_bis(self):
            pass

        def teardown_suite(self):
            marker.append("must_not_be_executed")

    report = run_suite_class(MySuite, fixtures=[fix])

    assert_test_statuses(report, skipped=["MySuite.sometest", "MySuite.sometest_bis"])
    assert not marker


def test_teardown_suite_error_because_of_exception():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            1 / 0

    report = run_suite_class(MySuite)

    assert_test_passed(report)
    assert_report_node_success(report, ReportLocation.in_suite_teardown("MySuite"), expected=False)


def test_teardown_suite_error_because_of_error_log():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_error("some error")

    report = run_suite_class(MySuite)

    assert_test_passed(report)
    assert_report_node_success(report, ReportLocation.in_suite_teardown("MySuite"), expected=False)


def test_teardown_suite_error_because_of_fixture():
    marker = []

    @lcc.fixture(scope="suite")
    def fix():
        yield 2
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

        def teardown_suite(self):
            marker.append("teardown")

    report = run_suite_class(MySuite, fixtures=[fix])

    assert_test_passed(report)
    assert_report_node_success(report, ReportLocation.in_suite_teardown("MySuite"), expected=False)
    assert len(marker) == 1


def test_setup_test_session_error_because_of_exception():
    @lcc.fixture(scope="session")
    def fixt():
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

        @lcc.test("Some other test")
        def sometest_bis(self):
            pass

    report = run_suite_class(MySuite, fixtures=[fixt])

    assert_test_statuses(report, skipped=["MySuite.sometest", "MySuite.sometest_bis"])
    assert_report_node_success(report, ReportLocation.in_test_session_setup(), expected=False)

    test_1, test_2 = list(report.all_tests())

    assert "test session setup failed" in test_1.status_details
    assert "test session setup failed" in test_2.status_details


def test_setup_test_session_error_and_setup_suite():
    marker = []

    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self, fixt):
            marker.append("setup_suite")

        @lcc.test("Some test")
        def sometest(self):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        1 / 0

    report = run_suite_class(MySuite, fixtures=[fixt])

    assert_test_skipped(report)
    assert_report_node_success(report, ReportLocation.in_test_session_setup(), expected=False)
    assert not marker


def test_teardown_test_session_error_because_of_exception():
    @lcc.fixture(scope="session")
    def fix():
        yield 1
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

        @lcc.test("Some other test")
        def sometest_bis(self):
            pass

    report = run_suite_class(MySuite, fixtures=[fix])

    assert_test_statuses(report, passed=["MySuite.sometest", "MySuite.sometest_bis"])
    assert_report_node_success(report, ReportLocation.in_test_session_teardown(), expected=False)


def test_teardown_test_session_after_test_failure():
    marker = []

    @lcc.fixture(scope="session")
    def fixt():
        yield 1
        marker.append(1)

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            1 / 0

    run_suite_class(MySuite, fixtures=[fixt])

    assert marker


def test_teardown_test_session_after_test_failure_and_test_success():
    marker = []

    @lcc.fixture(scope="session")
    def fixt():
        marker.append("test_session_setup")
        yield 1
        marker.append("test_session_teardown")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self, fixt):
            marker.append("test_1")
            1 / 0

        @lcc.test("Test 2")
        def test_2(self):
            marker.append("test_2")

    run_suite_class(MySuite, fixtures=[fixt])

    assert marker == ["test_session_setup", "test_1", "test_2", "test_session_teardown"]


def test_pre_run_fixture_exception():
    @lcc.fixture(scope="pre_run")
    def fix():
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    with pytest.raises(LemoncheesecakeException) as excinfo:
        report = run_suite_class(MySuite, fixtures=[fix])
        assert "Got an unexpected" in str(excinfo.value)
        assert_test_skipped(report)


def test_pre_run_fixture_user_error():
    @lcc.fixture(scope="pre_run")
    def fix():
        raise lcc.UserError("some error")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    with pytest.raises(LemoncheesecakeException) as excinfo:
        report = run_suite_class(MySuite, fixtures=[fix])
        assert str(excinfo.value) == "some error"
        assert_test_skipped(report)


def test_pre_run_fixture_teardown_exception():
    @lcc.fixture(scope="pre_run")
    def fix():
        yield
        1 / 0

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    with pytest.raises(LemoncheesecakeException) as excinfo:
        report = run_suite_class(MySuite, fixtures=[fix])
        assert "Got an unexpected" in str(excinfo.value)
        assert_test_passed(report)


def test_pre_run_fixture_teardown_user_error():
    @lcc.fixture(scope="pre_run")
    def fix():
        yield
        raise lcc.UserError("some error")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    with pytest.raises(LemoncheesecakeException) as excinfo:
        report = run_suite_class(MySuite, fixtures=[fix])
        assert str(excinfo.value) == "some error"
        assert_test_passed(report)


def test_run_with_fixture_using_test_method():
    marker = []

    @lcc.fixture()
    def test_fixture():
        return 1

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            marker.append(test_fixture)

    run_suite_class(MySuite, fixtures=[test_fixture])

    assert marker == [1]


def test_run_with_fixture_using_test_function():
    @lcc.fixture()
    def test_fixture():
        return 2

    suite = build_suite_from_module("""
@lcc.test("Test")
def test(test_fixture):
    lcc.log_info(str(test_fixture))
""")

    report = run_suite(suite, fixtures=[test_fixture])

    test = next(report.all_tests())
    assert test.get_steps()[0].get_logs()[0].message == "2"


def test_run_with_fixture_with_logs():
    marker = []

    @lcc.fixture()
    def test_fixture():
        lcc.log_info("setup")
        yield 1
        lcc.log_info("teardown")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            lcc.set_step("Doing some test")
            lcc.log_info("some log")
            marker.append(test_fixture)

    report = run_suite_class(MySuite, fixtures=[test_fixture])

    assert marker == [1]

    steps = report.get_suites()[0].get_tests()[0].get_steps()

    assert len(steps) == 3
    assert steps[0].description == "Setup test"
    assert steps[1].description == "Doing some test"
    assert steps[2].description == "Teardown test"


def test_run_with_fixtures_using_yield_and_dependencies():
    marker = []

    @lcc.fixture(scope="pre_run")
    def session_fixture_prerun():
        retval = 2
        marker.append(retval)
        yield retval
        marker.append(1)

    @lcc.fixture(scope="session")
    def session_fixture(session_fixture_prerun):
        lcc.log_info("session_fixture_setup")
        retval = session_fixture_prerun * 3
        marker.append(retval)
        yield retval
        marker.append(2)
        lcc.log_info("session_fixture_teardown")

    @lcc.fixture(scope="suite")
    def suite_fixture(session_fixture):
        lcc.log_info("suite_fixture_setup")
        retval = session_fixture * 4
        marker.append(retval)
        yield retval
        marker.append(3)
        lcc.log_info("suite_fixture_teardown")

    @lcc.fixture(scope="test")
    def test_fixture(suite_fixture):
        lcc.log_info("test_fixture_setup")
        retval = suite_fixture * 5
        marker.append(retval)
        yield retval
        marker.append(4)
        lcc.log_info("test_fixture_teardown")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            marker.append(test_fixture * 6)

    report = run_suite_class(MySuite, fixtures=(session_fixture_prerun, session_fixture, suite_fixture, test_fixture))

    # test that each fixture value is passed to test or fixture requiring the fixture
    assert marker == [2, 6, 24, 120, 720, 4, 3, 2, 1]

    # check that each fixture and fixture teardown is properly executed in the right scope
    assert report.test_session_setup.get_steps()[0].get_logs()[0].message == "session_fixture_setup"
    assert report.test_session_teardown.get_steps()[0].get_logs()[0].message == "session_fixture_teardown"
    assert report.get_suites()[0].suite_setup.get_steps()[0].get_logs()[0].message == "suite_fixture_setup"
    assert report.get_suites()[0].suite_teardown.get_steps()[0].get_logs()[0].message == "suite_fixture_teardown"
    assert report.get_suites()[0].get_tests()[0].get_steps()[0].get_logs()[0].message == "test_fixture_setup"
    assert report.get_suites()[0].get_tests()[0].get_steps()[1].get_logs()[0].message == "test_fixture_teardown"


def test_run_with_fixtures_dependencies_in_test_pre_run_scope():
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type

    marker = []

    @lcc.fixture(names=["fixt_3"], scope="pre_run")
    def fixt3():
        return 2

    @lcc.fixture(names=["fixt_2"], scope="pre_run")
    def fixt2(fixt_3):
        return fixt_3 * 3

    @lcc.fixture(names=["fixt_1"], scope="pre_run")
    def fixt1(fixt_2):
        return fixt_2 * 4

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            marker.append(fixt_1)

    run_suite_class(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert marker == [24]


def test_run_with_fixtures_dependencies_in_test_session_scope():
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type

    marker = []

    @lcc.fixture(names=["fixt_3"], scope="session")
    def fixt3():
        return 2

    @lcc.fixture(names=["fixt_2"], scope="session")
    def fixt2(fixt_3):
        return fixt_3 * 3

    @lcc.fixture(names=["fixt_1"], scope="session")
    def fixt1(fixt_2):
        return fixt_2 * 4

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            marker.append(fixt_1)

    run_suite_class(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert marker == [24]


def test_run_with_fixtures_dependencies_in_suite_scope():
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type

    marker = []

    @lcc.fixture(names=["fixt_3"], scope="suite")
    def fixt3():
        return 2

    @lcc.fixture(names=["fixt_2"], scope="suite")
    def fixt2(fixt_3):
        return fixt_3 * 3

    @lcc.fixture(names=["fixt_1"], scope="suite")
    def fixt1(fixt_2):
        return fixt_2 * 4

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            marker.append(fixt_1)

    run_suite_class(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert marker == [24]


def test_run_with_fixtures_dependencies_in_test_scope():
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type

    marker = []

    @lcc.fixture(names=["fixt_3"], scope="test")
    def fixt3():
        return 2

    @lcc.fixture(names=["fixt_2"], scope="test")
    def fixt2(fixt_3):
        return fixt_3 * 3

    @lcc.fixture(names=["fixt_1"], scope="test")
    def fixt1(fixt_2):
        return fixt_2 * 4

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            marker.append(fixt_1)

    run_suite_class(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert marker == [24]


def test_run_with_suite_fixture_used_in_subsuite():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt1():
        yield 1
        marker.append(2)

    @lcc.suite("MySuiteA")
    class MySuiteA:
        @lcc.test("Test")
        def test(self, fixt1):
            marker.append(fixt1)

        @lcc.suite("MySuiteB")
        class MySuiteB:
            @lcc.test("Test")
            def test(self, fixt1):
                marker.append(fixt1)

            @lcc.suite("MySuiteC")
            class MySuiteC:
                @lcc.test("Test")
                def test(self, fixt1):
                    marker.append(fixt1)

    run_suite_class(MySuiteA, fixtures=[fixt1])

    assert marker == [1, 2, 1, 2, 1, 2]


def test_run_with_fixture_used_in_setup_suite():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt1():
        return 1

    @lcc.suite("MySuiteA")
    class MySuite:
        def setup_suite(self, fixt1):
            marker.append(fixt1)

        @lcc.test("sometest")
        def sometest(self):
            pass

    run_suite_class(MySuite, fixtures=[fixt1])

    assert marker == [1]


def test_run_with_fixture_injected_in_class():
    marker = []

    @lcc.fixture(scope="session")
    def fixt1():
        return 1

    @lcc.suite("MySuiteA")
    class MySuite:
        fixt1 = lcc.inject_fixture()

        @lcc.test("sometest")
        def sometest(self):
            marker.append(self.fixt1)

    report = run_suite_class(MySuite, fixtures=[fixt1])

    assert_test_passed(report)
    assert marker == [1]


def test_run_with_fixture_injected_in_class_and_fixture_name_arg():
    marker = []

    @lcc.fixture(scope="session")
    def fixt1():
        return 1

    @lcc.suite("MySuiteA")
    class MySuite:
        fxt = lcc.inject_fixture("fixt1")

        @lcc.test("sometest")
        def sometest(self):
            marker.append(self.fxt)

    report = run_suite_class(MySuite, fixtures=[fixt1])

    assert_test_passed(report)
    assert marker == [1]


def test_run_with_fixture_injected_in_module():
    @lcc.fixture(scope="suite")
    def fixt1():
        return "MARKER"

    suite = build_suite_from_module("""
fixt1 = lcc.inject_fixture()

@lcc.test("Some test")
def sometest():
    lcc.log_info(fixt1)
    """)

    report = run_suite(suite, fixtures=[fixt1])

    test = next(report.all_tests())
    assert test.get_steps()[0].get_logs()[0].message == "MARKER"


def test_run_with_fixture_per_thread():
    @lcc.fixture(scope="session", per_thread=True)
    def fixt():
        return object()

    witness = defaultdict(set)

    @lcc.suite()
    class Suite:
        @lcc.test()
        @lcc.parametrized({"value": value} for value in range(20))  # create 20 different tests
        def test(self, value, fixt):
            time.sleep(0.01)  # make sure that each thread will be able to execute some tests
            witness[threading.current_thread().ident].add(fixt)

    run_suite_class(Suite, fixtures=(fixt,), nb_threads=4)

    # make sure that for each test-thread, the same fixture actual value is returned:
    assert len(witness) >= 1
    for objects in witness.values():
        assert len(objects) == 1


def test_run_with_fixture_per_thread_logging():
    @lcc.fixture(scope="session", per_thread=True)
    def fixt():
        lcc.log_info("Fixture setup")
        yield 1
        lcc.log_info("Fixture teardown")

    @lcc.suite()
    class Suite:
        @lcc.test()
        def test(self, fixt):
            pass

    report = run_suite_class(Suite, fixtures=(fixt,))
    test = get_last_test(report)

    assert test.get_steps()[0].get_logs()[0].message == "Fixture setup"
    assert report.test_session_teardown.get_steps()[0].get_logs()[0].message == "Fixture teardown"


def test_fixture_called_multiple_times():
    marker = []

    @lcc.fixture(scope="test")
    def fixt():
        return 1

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("test 1")
        def test_1(self, fixt):
            marker.append(fixt)

        @lcc.test("test 2")
        def test_2(self, fixt):
            marker.append(fixt)

    run_suite_class(MySuite, fixtures=[fixt])

    assert marker == [1, 1]


def test_fixture_name_scopes():
    fixts = []

    @lcc.fixture(scope="session")
    def fixt_pre_run(fixture_name):
        fixts.append(fixture_name)

    @lcc.fixture(scope="session")
    def fixt_session(fixture_name, fixt_pre_run):
        fixts.append(fixture_name)

    @lcc.fixture(scope="suite")
    def fixt_suite(fixture_name, fixt_session):
        fixts.append(fixture_name)

    @lcc.fixture(scope="test")
    def fixt_test(fixture_name, fixt_suite):
        fixts.append(fixture_name)

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt_test):
            pass

    run_suite_class(suite, fixtures=[fixt_pre_run, fixt_session, fixt_suite, fixt_test])

    assert fixts == ["fixt_pre_run", "fixt_session", "fixt_suite", "fixt_test"]


def test_fixture_name_multiple_names():
    fixts = []

    @lcc.fixture(scope="test", names=["fixt1", "fixt2"])
    def fixt(fixture_name):
        fixts.append(fixture_name)

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt1, fixt2):
            pass

    run_suite_class(suite, fixtures=[fixt])

    assert sorted(fixts) == ["fixt1", "fixt2"]


def test_fixture_with_test_scope_on_disabled_test():
    marker = []

    @lcc.fixture(scope="test")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt])
    assert_test_statuses(report, disabled=["suite.test_1"], passed=["suite.test_2"])

    assert not marker


def test_fixture_with_suite_scope_on_disabled_test():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt])
    assert_test_statuses(report, disabled=["suite.test_1"], passed=["suite.test_2"])

    assert not marker


def test_fixture_with_suite_scope_on_disabled_test_and_force_disabled():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt], force_disabled=True)
    assert_test_statuses(report, passed=["suite.test_1", "suite.test_2"])

    assert marker


def test_fixture_with_session_scope_on_disabled_test():
    marker = []

    @lcc.fixture(scope="session")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt])
    assert_test_statuses(report, disabled=["suite.test_1"], passed=["suite.test_2"])

    assert not marker


def test_fixture_with_session_scope_on_disabled_test_and_force_disabled():
    marker = []

    @lcc.fixture(scope="session")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt], force_disabled=True)
    assert_test_statuses(report, passed=["suite.test_1", "suite.test_2"])

    assert marker


def test_fixture_with_pre_run_scope_on_disabled_test():
    marker = []

    @lcc.fixture(scope="pre_run")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt])
    assert_test_statuses(report, disabled=["suite.test_1"], passed=["suite.test_2"])

    assert not marker


def test_fixture_with_pre_run_scope_on_disabled_test_and_force_disabled():
    marker = []

    @lcc.fixture(scope="pre_run")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        @lcc.disabled()
        def test_1(self, fixt):
            pass

        @lcc.test("test 2")
        def test_2(self):
            pass

    report = run_suite_class(suite, fixtures=[fixt], force_disabled=True)
    assert_test_statuses(report, passed=["suite.test_1", "suite.test_2"])

    assert marker


def test_fixture_in_suite_with_disabled_test():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite_1")
    class suite_1:
        fixt = lcc.inject_fixture()

        @lcc.test("test")
        @lcc.disabled()
        def test(self, fixt):
            pass

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2), fixtures=[fixt])
    assert_test_statuses(report, disabled=["suite_1.test"], passed=["suite_2.test"])

    assert not marker


def test_fixture_in_suite_with_disabled_test_and_force_disabled():
    marker = []

    @lcc.fixture(scope="suite")
    def fixt():
        marker.append("i've been executed")

    @lcc.suite("suite_1")
    class suite_1:
        fixt = lcc.inject_fixture()

        @lcc.test("test")
        @lcc.disabled()
        def test(self, fixt):
            pass

    @lcc.suite("suite_2")
    class suite_2:
        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_classes((suite_1, suite_2), fixtures=[fixt], force_disabled=True)
    assert_test_statuses(report, passed=["suite_1.test", "suite_2.test"])

    assert marker


def test_fixture_evaluation_order():
    @lcc.fixture()
    def a():
        lcc.log_info("a")

    @lcc.fixture()
    def b():
        lcc.log_info("b")

    @lcc.fixture()
    def c(b):
        lcc.log_info("c")

    @lcc.suite()
    class suite:
        @lcc.test()
        def test(self, a, c):
            pass

    report = run_suite_class(suite, fixtures=(a, b, c))

    test = get_last_test(report)

    assert [e.message for e in test.get_steps()[0].get_logs()] == ["a", "b", "c"]


def test_fixture_teardown_order():
    marker = []

    @lcc.fixture(scope="pre_run")
    def fixt_pre_run_1():
        yield None
        marker.append("fixt_pre_run_1")

    @lcc.fixture(scope="pre_run")
    def fixt_pre_run_2():
        yield None
        marker.append("fixt_pre_run_2")

    @lcc.fixture(scope="session")
    def fixt_session_1():
        yield None
        marker.append("fixt_session_1")

    @lcc.fixture(scope="session")
    def fixt_session_2():
        yield None
        marker.append("fixt_session_2")

    @lcc.fixture(scope="suite")
    def fixt_suite_1():
        yield None
        marker.append("fixt_suite_1")

    @lcc.fixture(scope="suite")
    def fixt_suite_2():
        yield None
        marker.append("fixt_suite_2")

    @lcc.fixture(scope="test")
    def fixt_test_1():
        yield None
        marker.append("fixt_test_1")

    @lcc.fixture(scope="test")
    def fixt_test_2():
        yield None
        marker.append("fixt_test_2")

    @lcc.suite()
    class suite:
        @lcc.test()
        def test(self,
                 fixt_pre_run_1, fixt_session_1, fixt_suite_1, fixt_test_1,
                 fixt_pre_run_2, fixt_session_2, fixt_suite_2, fixt_test_2):
            pass

    run_suite_class(suite, (fixt_pre_run_1, fixt_session_1, fixt_suite_1, fixt_test_1,
                            fixt_pre_run_2, fixt_session_2, fixt_suite_2, fixt_test_2))

    assert marker == [
        "fixt_test_2", "fixt_test_1",
        "fixt_suite_2", "fixt_suite_1",
        "fixt_session_2", "fixt_session_1",
        "fixt_pre_run_2", "fixt_pre_run_1"
    ]


def test_parametrized_simple():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized([{"value": "foo"}])
        def test(self, value):
            lcc.log_info(value)

    report = run_suite_class(suite)

    test = get_last_test(report)
    assert test.name == "test_1"
    assert test.description == "test #1"

    log = get_last_log(report)
    assert log.message == "foo"


def test_parametrized_with_multiple_test_and_fixture():
    @lcc.fixture(scope="session")
    def fixt():
        return "something"

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized([{"value_1": "foo", "value_2": "bar"}, {"value_1": "baz", "value_2": "foo"}])
        def test(self, value_1, value_2, fixt):
            lcc.log_info(value_1)
            lcc.log_info(value_2)
            lcc.log_info(fixt)

    report = run_suite_class(suite, fixtures=[fixt])

    test_1, test_2 = report.all_tests()

    assert test_1.name == "test_1"
    assert test_1.description == "test #1"
    assert test_1.get_steps()[0].get_logs()[0].message == "foo"
    assert test_1.get_steps()[0].get_logs()[1].message == "bar"
    assert test_1.get_steps()[0].get_logs()[2].message == "something"

    assert test_2.name == "test_2"
    assert test_2.description == "test #2"
    assert test_2.get_steps()[0].get_logs()[0].message == "baz"
    assert test_2.get_steps()[0].get_logs()[1].message == "foo"
    assert test_2.get_steps()[0].get_logs()[2].message == "something"


def test_parametrized_extra_param():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized([{"value": "foo", "extra": "bar"}])
        def test(self, value):
            lcc.log_info(value)

    report = run_suite_class(suite)

    test = get_last_test(report)
    assert test.name == "test_1"
    assert test.description == "test #1"

    log = get_last_log(report)
    assert log.message == "foo"


def test_stop_on_failure_test():
    @lcc.suite("Suite")
    class suite:
        @lcc.test("Test 1")
        def test1(self):
            1 / 0
        
        @lcc.test("Test 2")
        def test2(self):
            pass

    report = run_suite_class(suite, stop_on_failure=True)

    assert_test_statuses(report, failed=["suite.test1"], skipped=["suite.test2"])


def test_stop_on_failure_suite_setup():
    @lcc.suite("Suite 1")
    class suite1:
        def setup_suite(self):
            1 / 0
        
        @lcc.test("Test 1")
        def test1(self):
            pass
    
    @lcc.suite("Suite 2")
    class suite2:
        @lcc.test("Test 2")
        def test2(self):
            pass

    report = run_suite_classes([suite1, suite2], stop_on_failure=True)

    assert_test_statuses(report, skipped=["suite1.test1", "suite2.test2"])


def test_stop_on_failure_suite_teardown():
    @lcc.suite("Suite 1")
    class suite1:
        @lcc.test("Test 1")
        def test1(self):
            pass

        def teardown_suite(self):
            1 / 0
        
    @lcc.suite("Suite 2")
    class suite2:
        @lcc.test("Test 2")
        def test2(self):
            pass

    report = run_suite_classes([suite1, suite2], stop_on_failure=True)

    assert_test_statuses(report, passed=["suite1.test1"], skipped=["suite2.test2"])


def test_disabled_test():
    @lcc.suite("Suite")
    class mysuite:
        @lcc.test("Test")
        @lcc.disabled()
        def mytest(self):
            pass

    report = run_suite_class(mysuite)

    assert_test_statuses(report, disabled=["mysuite.mytest"])


def test_disabled_test_with_reason():
    @lcc.suite("Suite")
    class mysuite:
        @lcc.test("Test")
        @lcc.disabled("some reason")
        def mytest(self):
            pass

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "disabled"
    assert test.status_details == "some reason"


def test_disabled_test_with_force_disabled():
    @lcc.suite("Suite")
    class mysuite:
        @lcc.test("Test")
        @lcc.disabled()
        def mytest(self):
            pass

    report = run_suite_class(mysuite, force_disabled=True)

    assert_test_statuses(report, passed=["mysuite.mytest"])


def test_disabled_suite():
    @lcc.suite("Suite")
    @lcc.disabled()
    class mysuite:
        @lcc.test("Test 1")
        def test1(self):
            pass

        @lcc.test("Test 2")
        def test2(self):
            pass

    report = run_suite_class(mysuite)

    assert_test_statuses(report, disabled=["mysuite.test1", "mysuite.test2"])


def test_disabled_suite_with_reason():
    @lcc.suite("Suite")
    @lcc.disabled("some reason")
    class mysuite:
        @lcc.test("Test 1")
        def test1(self):
            pass

        @lcc.test("Test 2")
        def test2(self):
            pass

    report = run_suite_class(mysuite)
    test_1, test_2 = list(report.all_tests())
    assert test_1.status == test_2.status == "disabled"
    assert test_1.status_details == test_2.status_details == "some reason"


def test_disabled_in_skipped_suite():
    @lcc.suite("Suite")
    class mysuite:
        def setup_suite(self):
            lcc.log_error("something wrong happened")

        @lcc.test("Test 1")
        def test1(self):
            pass

        @lcc.test("Test 2")
        @lcc.disabled()
        def test2(self):
            pass

    report = run_suite_class(mysuite)

    assert_test_statuses(report, skipped=["mysuite.test1"], disabled=["mysuite.test2"])


def test_get_fixture():
    marker = []

    @lcc.fixture(scope="pre_run")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self, fixt):
            marker.append(lcc.get_fixture("fixt"))

    run_suite_class(mysuite, fixtures=[fixt])

    assert marker == [42]


def test_get_fixture_bad_scope():
    marker = []

    @lcc.fixture(scope="test")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self, fixt):
            try:
                lcc.get_fixture("fixt")
            except LookupError:
                marker.append("exception")

    run_suite_class(mysuite, fixtures=[fixt])

    assert marker == ["exception"]


def test_get_fixture_unknown():
    marker = []

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            try:
                lcc.get_fixture("fixt")
            except LookupError:
                marker.append("exception")

    run_suite_class(mysuite)

    assert marker == ["exception"]


def test_get_fixture_not_executed():
    marker = []

    @lcc.fixture(scope="pre_run")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            try:
                lcc.get_fixture("fixt")
            except LookupError:
                marker.append("exception")

    run_suite_class(mysuite)

    assert marker == ["exception"]


def test_exception_in_reporting_backend(tmpdir):
    class MyException(Exception):
        pass

    class MyReportingSession(ReportingSession):
        def on_log(self, event):
            raise MyException()

    class MyReportingBackend(ReportingBackend):
        def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
            return MyReportingSession()

    @lcc.suite("MySuite")
    class mysuite(object):
        @lcc.test("mytest")
        def mytest(self):
            lcc.log_info("some log")

    with pytest.raises(MyException) as excinfo:
        run_suite_class(mysuite, backends=[MyReportingBackend()], tmpdir=tmpdir)


# this bug was provoke a freeze and was introduced in 0.21.0 and fixed in 0.22.3
def test_bug_in_task_handling():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test 1")
        def test_1(self):
            lcc.log_error("error")

        @lcc.test("test 2")
        def test_2(self):
            lcc.log_error("error")

        @lcc.test("test 3")
        def test_3(self):
            pass

    report = run_suite_class(suite)

    assert_test_statuses(report, failed=["suite.test_1", "suite.test_2"], passed=["suite.test_3"])


def test_depends_on_passed():
    @lcc.suite("s")
    class suite:
        @lcc.test("t1")
        def test1(self):
            pass

        @lcc.test("t2")
        @lcc.depends_on("suite.test1")
        def test2(self):
            pass

    report = run_suite_class(suite)

    assert_test_statuses(report, passed=["suite.test1", "suite.test2"])


def test_depends_on_failed_exception():
    @lcc.suite("s")
    class suite:
        @lcc.test("t1")
        def test1(self):
            raise Exception()

        @lcc.test("t2")
        @lcc.depends_on("suite.test1")
        def test2(self):
            pass

        @lcc.test("t3")
        def test3(self):
            pass

    report = run_suite_class(suite)

    assert_test_statuses(report, failed=["suite.test1"], skipped=["suite.test2"], passed=["suite.test3"])


def test_depends_on_failed_failure():
    @lcc.suite("s")
    class suite:
        @lcc.test("t1")
        def test1(self):
            lcc.log_error("some error")

        @lcc.test("t2")
        @lcc.depends_on(lambda t: t.path == "suite.test1")
        def test2(self):
            pass

        @lcc.test("t3")
        def test3(self):
            pass

    report = run_suite_class(suite)

    assert_test_statuses(report, failed=["suite.test1"], skipped=["suite.test2"], passed=["suite.test3"])


def test_depends_on_skipped():
    @lcc.suite("s")
    class suite:
        @lcc.test("t1")
        def test1(self):
            lcc.log_error("some error")

        @lcc.test("t2")
        @lcc.depends_on("suite.test1")
        def test2(self):
            pass

        @lcc.test("t3")
        @lcc.depends_on("suite.test2")
        def test3(self):
            pass

    report = run_suite_class(suite)

    assert_test_statuses(report, failed=["suite.test1"], skipped=["suite.test2", "suite.test3"])


def test_depends_on_failed_and_subsuite():
    @lcc.suite("s1")
    class suite1:
        @lcc.test("t1")
        def test1(self):
            lcc.log_error("some error")

        @lcc.suite("s2")
        class suite2:
            @lcc.test("t2")
            @lcc.depends_on("suite1.test1")
            def test2(self):
                pass

    report = run_suite_class(suite1)

    assert_test_statuses(report, failed=["suite1.test1"], skipped=["suite1.suite2.test2"])


