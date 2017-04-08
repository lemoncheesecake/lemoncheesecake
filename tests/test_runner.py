'''
Created on Sep 30, 2016

@author: nicolas
'''

import os
import sys
import tempfile
import shutil

import pytest

from lemoncheesecake import runner
from lemoncheesecake.testsuite import Filter, load_testsuites_from_classes
from lemoncheesecake.worker import Worker
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import *
import lemoncheesecake.api as lcc
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string

from helpers import reporting_session, run_testsuite, build_fixture_registry
from lemoncheesecake.fixtures import FixtureRegistry
from lemoncheesecake.testsuite import add_test_in_testsuite

# TODO: make launcher unit tests more independent from the reporting layer ?

def assert_report_errors(errors):
    stats = get_runtime().report.get_stats()
    assert stats.errors == errors

def test_test_success(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_last_test_outcome() == True

def test_test_failure(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_eq("val", 1, 2)
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_last_test_outcome() == False

def test_exception_unexpected(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("First test")
        def first_test(self):
            1 / 0
        
        @lcc.test("Second test")
        def second_test(self):
            pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("first_test") == False
    assert reporting_session.get_test_outcome("second_test") == True

def test_exception_aborttest(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            raise lcc.AbortTest("test error")
    
        @lcc.test("Some other test")
        def someothertest(self):
            pass
        
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("sometest") == False
    assert reporting_session.get_test_outcome("someothertest") == True

def test_exception_aborttestsuite(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.testsuite("MyFirstSuite")
        class MyFirstSuite:
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortTestSuite("test error")
        
            @lcc.test("Some other test")
            def someothertest(self):
                pass
        
        @lcc.testsuite("MySecondSuite")
        class MySecondSuite:
            @lcc.test("Another test")
            def anothertest(self):
                pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("sometest") == False
    assert reporting_session.get_test_outcome("someothertest") == False
    assert reporting_session.get_test_outcome("anothertest") == True

def test_exception_abortalltests(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.testsuite("MyFirstSuite")
        class MyFirstSuite:
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortAllTests("test error")
        
            @lcc.test("Some other test")
            def someothertest(self):
                pass
        
        @lcc.testsuite("MySecondSuite")
        class MySecondSuite:
            @lcc.test("Another test")
            def anothertest(self):
                pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("sometest") == False
    assert reporting_session.get_test_outcome("someothertest") == False
    assert reporting_session.get_test_outcome("anothertest") == False

def test_generated_test(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def __init__(self):
            def test_func(suite):
                lcc.log_info("somelog")
            test = lcc.Test("mytest", "My Test", test_func)
            add_test_in_testsuite(test, self)
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("mytest")

def test_sub_testsuite_inline(reporting_session):
    @lcc.testsuite("MyParentSuite")
    class MyParentSuite:
        @lcc.testsuite("MyChildSuite")
        class MyChildSuite:
            @lcc.test("Some test")
            def sometest(self):
                pass
    
    run_testsuite(MyParentSuite)
    
    assert reporting_session.get_test_outcome("sometest") == True

def test_sub_testsuite_attr(reporting_session):
    @lcc.testsuite("MyChildSuite")
    class MyChildSuite:
            @lcc.test("Some test")
            def sometest(self):
                pass
    @lcc.testsuite("MyParentSuite")
    class MyParentSuite:
        sub_suites = [MyChildSuite]
    
    run_testsuite(MyParentSuite)
    
    assert reporting_session.get_test_outcome("sometest") == True

def test_worker_accessible_through_testsuite(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            assert self.testworker != None
    
    class MyWorker(Worker):
        pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_test_outcome() == True

def test_worker_accessible_through_runtime(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            assert lcc.get_worker("testworker") != None
    
    class MyWorker(Worker):
        pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_test_outcome() == True

def test_setup_test_session(reporting_session):
    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_info("hook called")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_log() == "hook called"

def test_teardown_test_session(reporting_session):
    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.log_info("hook called")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_log() == "hook called"

def test_setup_test(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_teardown_test(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def teardown_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_setup_suite(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_teardown_suite(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def teardown_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_setup_test_error(reporting_session):
    marker = []
    
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass
        
        def teardown_test(self, test_name):
            marker.append(test_name)

    run_testsuite(MySuite)

    assert reporting_session.get_test_outcome("sometest") == False
    assert len(marker) == 0

def test_setup_test_error_in_fixture(reporting_session):
    @lcc.fixture()
    def fix():
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    run_testsuite(MySuite, fixtures=[fix])

    assert reporting_session.get_test_outcome("sometest") == False


def test_teardown_test_error(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        def teardown_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_test_outcome("sometest") == False

def test_teardown_test_error_in_fixture(reporting_session):
    @lcc.fixture()
    def fix():
        1 / 0

    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    run_testsuite(MySuite, fixtures=[fix])

    assert reporting_session.get_test_outcome("sometest") == False

def test_setup_suite_error_and_subsuite(reporting_session):
    marker = []
    
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            1 / 0
        
        @lcc.test("test")
        def test(self):
            marker.append("suite")
        
        @lcc.testsuite("MySubSuite")
        class MySubSuite:
            @lcc.test("test")
            def test(self):
                marker.append("sub_suite")
        
    run_testsuite(MySuite)

    assert marker == ["sub_suite"]

def test_setup_suite_error_because_of_exception(reporting_session):
    marker = []
    
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass
        
        def teardown_suite(self):
            marker.append("suite_teardown")
        
    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)
    assert len(marker) == 0

def test_setup_suite_error_because_of_error_log(reporting_session):
    marker = []

    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_error("some error")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            marker.append("teardown")

    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)
    assert len(marker) == 0

def test_setup_suite_error_because_of_fixture(reporting_session):
    marker = []
    
    @lcc.fixture(scope="testsuite")
    def fix():
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
        
        @lcc.test("Some other test")
        def sometest_bis(self):
            pass
        
        def teardown_suite(self):
            marker.append("must_not_be_executed")

    run_testsuite(MySuite, fixtures=[fix])

    assert reporting_session.get_failing_test_nb() == 2
    assert_report_errors(1)
    assert len(marker) == 0

def test_teardown_suite_error_because_of_exception(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            1 / 0
        
    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)

def test_teardown_suite_error_because_of_error_log(reporting_session):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_error("some error")
        
    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)

def test_teardown_suite_error_because_of_fixture(reporting_session):
    marker = []

    @lcc.fixture(scope="testsuite")
    def fix():
        yield 2
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
        
        def teardown_suite(self):
            marker.append("teardown")

    run_testsuite(MySuite, fixtures=[fix])

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)
    assert len(marker) == 1

def test_setup_test_session_error_because_of_exception(reporting_session):
    marker = []
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            1 / 0
        
        def teardown_test_session(self):
            marker.append("teardown")

    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)
    assert len(marker) == 0

def test_setup_test_session_error_because_of_fixture(reporting_session):
    marker = []
    
    @lcc.fixture(scope="session")
    def fix():
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
        
        @lcc.test("Some other test")
        def sometest_bis(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            marker.append("setup")
        
        def teardown_test_session(self):
            marker.append("teardown")

    run_testsuite(MySuite, fixtures=[fix], worker=MyWorker())

    assert reporting_session.get_failing_test_nb() == 2
    assert_report_errors(1)
    assert "teardown" in marker

def test_setup_test_session_error_and_setup_suite(reporting_session):
    marker = []
    
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            marker.append("setup_suite")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            1 / 0

    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)
    assert len(marker) == 0

def test_teardown_test_session_error_because_of_exception(reporting_session):
    marker = []
    
    @lcc.fixture()
    def fix():
        yield 1
        marker.append("teardown")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    class MyWorker(Worker):
        def teardown_test_session(self):
            1 / 0
            
    run_testsuite(MySuite, worker=MyWorker(), fixtures=[fix])

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)
    assert "teardown" in marker

def test_teardown_test_session_error_because_of_error_log(reporting_session):
    marker = []
    
    @lcc.fixture()
    def fix():
        yield 1
        marker.append("teardown")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass

    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.log_error("some error")
        
    run_testsuite(MySuite, worker=MyWorker(), fixtures=[fix])

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)
    assert "teardown" in marker

def test_teardown_test_session_error_because_of_fixture(reporting_session):
    marker = []
    
    @lcc.fixture(scope="session")
    def fix():
        yield 1
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
        
        @lcc.test("Some other test")
        def sometest_bis(self):
            pass
    
    class MyWorker(Worker):
        def teardown_test_session(self):
            marker.append("teardown")
    
    run_testsuite(MySuite, fixtures=[fix], worker=MyWorker())

    assert reporting_session.get_successful_test_nb() == 2
    assert_report_errors(1)
    assert "teardown" in marker

def test_session_prerun_fixture_exception(reporting_session):
    @lcc.fixture(scope="session_prerun")
    def fix():
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
    
    with pytest.raises(LemonCheesecakeException) as excinfo:    
        run_testsuite(MySuite, fixtures=[fix])
        assert "Got an unexpected" in str(excinfo.value)

    assert reporting_session.test_nb == 0

def test_session_prerun_fixture_user_error(reporting_session):
    @lcc.fixture(scope="session_prerun")
    def fix():
        raise lcc.UserError("some error")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
    
    with pytest.raises(LemonCheesecakeException) as excinfo:    
        run_testsuite(MySuite, fixtures=[fix])
        assert str(excinfo.value) == "some error"

    assert reporting_session.test_nb == 0

def test_session_prerun_fixture_teardown_exception(reporting_session):
    @lcc.fixture(scope="session_prerun")
    def fix():
        yield
        1 / 0
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
    
    with pytest.raises(LemonCheesecakeException) as excinfo:    
        run_testsuite(MySuite, fixtures=[fix])
        assert "Got an unexpected" in str(excinfo.value)

    assert reporting_session.test_nb == 1

def test_session_prerun_fixture_teardown_user_error(reporting_session):
    @lcc.fixture(scope="session_prerun")
    def fix():
        yield
        raise lcc.UserError("some error")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fix):
            pass
    
    with pytest.raises(LemonCheesecakeException) as excinfo:    
        run_testsuite(MySuite, fixtures=[fix])
        assert str(excinfo.value) == "some error"

    assert reporting_session.test_nb == 1

def test_run_with_fixture():
    marker = []
    
    @lcc.fixture()
    def test_fixture():
        retval = 2
        marker.append(retval)
        return retval
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            marker.append(test_fixture * 3)
        
    run_testsuite(MySuite, fixtures=[test_fixture])
    
    assert marker == [2, 6]

def test_run_with_fixture_with_logs():
    marker = []
    
    @lcc.fixture()
    def test_fixture():
        lcc.log_info("setup")
        retval = 2
        marker.append(retval)
        yield retval
        lcc.log_info("teardown")
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            lcc.set_step("Doing some test")
            lcc.log_info("some log")
            marker.append(test_fixture * 3)
    
    run_testsuite(MySuite, fixtures=[test_fixture])
    
    assert marker == [2, 6]
    
    report = get_runtime().report
    
    assert len(report.testsuites[0].tests[0].steps) == 3
    assert report.testsuites[0].tests[0].steps[0].description == "Setup test"
    assert report.testsuites[0].tests[0].steps[1].description == "Doing some test"
    assert report.testsuites[0].tests[0].steps[2].description == "Teardown test"

def test_run_with_fixtures_using_yield_and_dependencies():
    marker = []
    
    @lcc.fixture(scope="session_prerun")
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
    
    @lcc.fixture(scope="testsuite")
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
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, test_fixture):
            marker.append(test_fixture * 6)
    
    run_testsuite(MySuite, fixtures=(session_fixture_prerun, session_fixture, suite_fixture, test_fixture))
    
    # test that each fixture value is passed to test or fixture requiring the fixture
    assert marker == [2, 6, 24, 120, 720, 4, 3, 2, 1]
    
    report = get_runtime().report
    
    # check that each fixture and fixture teardown is properly executed in the right scope
    assert report.test_session_setup.steps[0].entries[0].message == "session_fixture_setup"
    assert report.test_session_teardown.steps[0].entries[0].message == "session_fixture_teardown"
    assert report.testsuites[0].suite_setup.steps[0].entries[0].message == "suite_fixture_setup"
    assert report.testsuites[0].suite_teardown.steps[0].entries[0].message == "suite_fixture_teardown"
    assert report.testsuites[0].tests[0].steps[0].entries[0].message == "test_fixture_setup"
    assert report.testsuites[0].tests[0].steps[1].entries[0].message == "test_fixture_teardown"

def test_run_with_fixtures_dependencies_in_test_session_prerun_scope(reporting_session):
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type  
    
    @lcc.fixture(names=["fixt_3"], scope="session_prerun")
    def fixt3():
        return 2
    
    @lcc.fixture(names=["fixt_2"], scope="session_prerun")
    def fixt2(fixt_3):
        return fixt_3 * 3
    
    @lcc.fixture(names=["fixt_1"], scope="session_prerun")
    def fixt1(fixt_2):
        return fixt_2 * 4
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            assert fixt_1 == 24
    
    run_testsuite(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert reporting_session.get_successful_test_nb() == 1

def test_run_with_fixtures_dependencies_in_test_session_scope(reporting_session):
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type  
    
    @lcc.fixture(names=["fixt_3"], scope="session")
    def fixt3():
        return 2
    
    @lcc.fixture(names=["fixt_2"], scope="session")
    def fixt2(fixt_3):
        return fixt_3 * 3
    
    @lcc.fixture(names=["fixt_1"], scope="session")
    def fixt1(fixt_2):
        return fixt_2 * 4
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            assert fixt_1 == 24
    
    run_testsuite(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert reporting_session.get_successful_test_nb() == 1

def test_run_with_fixtures_dependencies_in_suite_scope(reporting_session):
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type  
    
    @lcc.fixture(names=["fixt_3"], scope="testsuite")
    def fixt3():
        return 2
    
    @lcc.fixture(names=["fixt_2"], scope="testsuite")
    def fixt2(fixt_3):
        return fixt_3 * 3
    
    @lcc.fixture(names=["fixt_1"], scope="testsuite")
    def fixt1(fixt_2):
        return fixt_2 * 4
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            assert fixt_1 == 24
    
    run_testsuite(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert reporting_session.get_successful_test_nb() == 1

def test_run_with_fixtures_dependencies_in_test_scope(reporting_session):
    # in this test, fixture dependency is set on fixture alphabetical inverse
    # order to highlight a bad dependency check implementation that use set data type  
    
    @lcc.fixture(names=["fixt_3"], scope="test")
    def fixt3():
        return 2
    
    @lcc.fixture(names=["fixt_2"], scope="test")
    def fixt2(fixt_3):
        return fixt_3 * 3
    
    @lcc.fixture(names=["fixt_1"], scope="test")
    def fixt1(fixt_2):
        return fixt_2 * 4
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test")
        def test(self, fixt_1):
            assert fixt_1 == 24
    
    run_testsuite(MySuite, fixtures=[fixt1, fixt2, fixt3])

    assert reporting_session.get_successful_test_nb() == 1

def test_run_with_testsuite_fixture_used_in_subsuite(reporting_session):
    teardowns = []
    
    @lcc.fixture(scope="testsuite")
    def fixt1():
        yield 2
        teardowns.append(True)
    
    @lcc.testsuite("MySuiteA")
    class MySuiteA:
        @lcc.test("Test")
        def test(self, fixt1):
            assert fixt1 == 2
        
        @lcc.testsuite("MySuiteB")
        class MySuiteB:
            @lcc.test("Test")
            def test(self, fixt1):
                assert fixt1 == 2

            @lcc.testsuite("MySuiteC")
            class MySuiteC:
                @lcc.test("Test")
                def test(self, fixt1):
                    assert fixt1 == 2
    
    run_testsuite(MySuiteA, fixtures=[fixt1])
    
    assert reporting_session.get_successful_test_nb() == 3
    assert len(teardowns) == 3

def test_run_with_fixture_used_in_setup_suite(reporting_session):
    marker = []
      
    @lcc.fixture(scope="testsuite")
    def fixt1():
        return "setup_suite"
      
    @lcc.testsuite("MySuiteA")
    class MySuite:
        def setup_suite(self, fixt1):
            marker.append(fixt1)
         
        @lcc.test("sometest")
        def sometest(self):
            pass
      
    run_testsuite(MySuite, fixtures=[fixt1])
      
    assert reporting_session.get_successful_test_nb() == 1
    assert marker[0] == "setup_suite"

def test_fixture_called_multiple_times(reporting_session):
    marker = [0]
    @lcc.fixture(scope="test")
    def fixt():
        marker[0] += 1
        return marker[0]
    
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("test 1")
        def test_1(self, fixt):
            assert fixt == 1
        
        @lcc.test("test 2")
        def test_2(self, fixt):
            assert fixt == 2
    
    run_testsuite(MySuite, fixtures=[fixt])
    
    assert reporting_session.get_successful_test_nb() == 2

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
    
    @lcc.fixture(scope="testsuite")
    def fixt_for_testsuite1(fixt_for_session1):
        pass

    @lcc.fixture(scope="testsuite")
    def fixt_for_testsuite2(fixt_for_session2):
        pass

    @lcc.fixture(scope="test")
    def fixt_for_test1(fixt_for_testsuite1):
        pass
    
    @lcc.fixture(scope="test")
    def fixt_for_test2(fixt_for_test1):
        pass
    
    @lcc.fixture(scope="test")
    def fixt_for_test3(fixt_for_session2):
        pass

    return build_fixture_registry(
        fixt_for_session_prerun1, fixt_for_session1, fixt_for_session2, fixt_for_session3,
        fixt_for_testsuite1, fixt_for_testsuite2,
        fixt_for_test1, fixt_for_test2, fixt_for_test3
    )

@pytest.fixture()
def testsuites_sample():
    @lcc.testsuite("suite1")
    class suite1:
        @lcc.test("Test 1")
        def suite1_test1(self, fixt_for_testsuite1):
            pass
        
        @lcc.test("Test 2")
        def suite1_test2(self, fixt_for_test3):
            pass
        
    @lcc.testsuite("suite2")
    class suite2:
        @lcc.test("Test 1")
        def suite2_test1(self, fixt_for_test2):
            pass
    
    return load_testsuites_from_classes([suite1, suite2])

def test_get_fixtures_to_be_executed_for_session_prerun(fixture_registry_sample, testsuites_sample):
    run = runner._Runner(testsuites_sample, fixture_registry_sample, [], [], None)
    
    assert sorted(run.get_fixtures_to_be_executed_for_session_prerun()) == ["fixt_for_session_prerun1"]

def test_get_fixtures_to_be_executed_for_session(fixture_registry_sample, testsuites_sample):
    run = runner._Runner(testsuites_sample, fixture_registry_sample, [], [], None)
    
    assert sorted(run.get_fixtures_to_be_executed_for_session()) == ["fixt_for_session1", "fixt_for_session2"]

def test_get_fixtures_to_be_executed_for_testsuite(fixture_registry_sample, testsuites_sample):
    run = runner._Runner(testsuites_sample, fixture_registry_sample, [], [], None)
    
    assert sorted(run.get_fixtures_to_be_executed_for_testsuite(testsuites_sample[0])) == ["fixt_for_testsuite1"]
    assert sorted(run.get_fixtures_to_be_executed_for_testsuite(testsuites_sample[1])) == ["fixt_for_testsuite1"]

def test_get_fixtures_to_be_executed_for_test(fixture_registry_sample, testsuites_sample):
    run = runner._Runner(testsuites_sample, fixture_registry_sample, [], [], None)
    
    assert sorted(run.get_fixtures_to_be_executed_for_test(testsuites_sample[0].get_tests()[0])) == []
    assert sorted(run.get_fixtures_to_be_executed_for_test(testsuites_sample[0].get_tests()[1])) == ["fixt_for_test3"]
    assert sorted(run.get_fixtures_to_be_executed_for_test(testsuites_sample[1].get_tests()[0])) == ["fixt_for_test1", "fixt_for_test2"]

def test_fixture_name_scopes():
    fixts = []

    @lcc.fixture(scope="session")
    def fixt_session_prerun(fixture_name):
        fixts.append(fixture_name)
    
    @lcc.fixture(scope="session")
    def fixt_session(fixture_name, fixt_session_prerun):
        fixts.append(fixture_name)

    @lcc.fixture(scope="testsuite")
    def fixt_suite(fixture_name, fixt_session):
        fixts.append(fixture_name)

    @lcc.fixture(scope="test")
    def fixt_test(fixture_name, fixt_suite):
        fixts.append(fixture_name)

    @lcc.testsuite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt_test):
            pass
    
    run_testsuite(suite, fixtures=[fixt_session_prerun, fixt_session, fixt_suite, fixt_test])

    assert fixts == ["fixt_session_prerun", "fixt_session", "fixt_suite", "fixt_test"]

def test_fixture_name_multiple_names():
    fixts = []
    
    @lcc.fixture(scope="test", names=["fixt1", "fixt2"])
    def fixt(fixture_name):
        fixts.append(fixture_name)

    @lcc.testsuite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt1, fixt2):
            pass
    
    run_testsuite(suite, fixtures=[fixt])

    assert sorted(fixts) == ["fixt1", "fixt2"]
