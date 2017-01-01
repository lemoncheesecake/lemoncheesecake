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
from lemoncheesecake.testsuite import Filter
from lemoncheesecake.worker import Worker
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import *
import lemoncheesecake as lcc
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string

from helpers import reporting_session, run_testsuite

# TODO: make launcher unit tests more independent from the reporting layer ?

def assert_report_errors(errors):
    stats = get_runtime().report.get_stats()
    assert stats.errors == errors

def test_test_success(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_last_test_outcome() == True

def test_test_failure(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_eq("val", 1, 2)
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_last_test_outcome() == False

def test_exception_unexpected(reporting_session):
    class MySuite(lcc.TestSuite):
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
    class MySuite(lcc.TestSuite):
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
    class MySuite(lcc.TestSuite):
        class MyFirstSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortTestSuite("test error")
        
            @lcc.test("Some other test")
            def someothertest(self):
                pass
        
        class MySecondSuite(lcc.TestSuite):
            @lcc.test("Another test")
            def anothertest(self):
                pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("sometest") == False
    assert reporting_session.get_test_outcome("someothertest") == False
    assert reporting_session.get_test_outcome("anothertest") == True

def test_exception_abortalltests(reporting_session):
    class MySuite(lcc.TestSuite):
        class MyFirstSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                raise lcc.AbortAllTests("test error")
        
            @lcc.test("Some other test")
            def someothertest(self):
                pass
        
        class MySecondSuite(lcc.TestSuite):
            @lcc.test("Another test")
            def anothertest(self):
                pass
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("sometest") == False
    assert reporting_session.get_test_outcome("someothertest") == False
    assert reporting_session.get_test_outcome("anothertest") == False

def test_generated_test(reporting_session):
    class MySuite(lcc.TestSuite):
        def load_generated_tests(self):
            def test_func(suite):
                lcc.log_info("somelog")
            test = lcc.Test("mytest", "My Test", test_func)
            self.register_test(test)
    
    run_testsuite(MySuite)
    
    assert reporting_session.get_test_outcome("mytest")

def test_sub_testsuite_inline(reporting_session):
    class MyParentSuite(lcc.TestSuite):
        class MyChildSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                pass
    
    run_testsuite(MyParentSuite)
    
    assert reporting_session.get_test_outcome("sometest") == True

def test_sub_testsuite_attr(reporting_session):
    class MyChildSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                pass
    class MyParentSuite(lcc.TestSuite):
        sub_suites = [MyChildSuite]
    
    run_testsuite(MyParentSuite)
    
    assert reporting_session.get_test_outcome("sometest") == True

def test_worker_accessible_through_testsuite(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            assert self.testworker != None
    
    class MyWorker(Worker):
        pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_test_outcome() == True

def test_worker_accessible_through_runtime(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            assert lcc.get_worker("testworker") != None
    
    class MyWorker(Worker):
        pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_test_outcome() == True

def test_hook_worker_before_all_tests(reporting_session):
    class MyWorker(Worker):
        def before_all_tests(self):
            lcc.log_info("hook called")
    
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_log() == "hook called"

def test_hook_worker_after_all_tests(reporting_session):
    class MyWorker(Worker):
        def after_all_tests(self):
            lcc.log_info("hook called")
    
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite, worker=MyWorker())
    
    assert reporting_session.get_last_log() == "hook called"

def test_hook_before_test(reporting_session):
    class MySuite(lcc.TestSuite):
        def before_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_hook_after_test(reporting_session):
    class MySuite(lcc.TestSuite):
        def after_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_hook_before_suite(reporting_session):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_hook_after_suite(reporting_session):
    class MySuite(lcc.TestSuite):
        def after_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_log() == "hook called"

def test_hook_error_before_test(reporting_session):
    class MySuite(lcc.TestSuite):
        def before_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_test_outcome("sometest") == False

def test_hook_error_after_test(reporting_session):
    class MySuite(lcc.TestSuite):
        def after_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_test_outcome("sometest") == False

def test_hook_error_before_suite_because_of_exception(reporting_session):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)

def test_hook_error_before_suite_because_of_error_log(reporting_session):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            lcc.log_error("some error")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)

def test_hook_error_after_suite_because_of_exception(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def after_suite(self):
            1 / 0
        
    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)

def test_hook_error_after_suite_because_of_error_log(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def after_suite(self):
            lcc.log_error("some error")
        
    run_testsuite(MySuite)

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)

def test_hook_error_worker_before_all_tests_because_of_exception(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def before_all_tests(self):
            1 / 0

    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)

def test_hook_error_worker_before_all_tests_because_of_error_log(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def before_all_tests(self):
            lcc.log_error("some error")

    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == False
    assert_report_errors(1)

def test_hook_error_worker_after_all_tests_because_of_exception(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def after_all_tests(self):
            1 / 0
            
    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)

def test_hook_error_worker_after_all_tests_because_of_error_log(reporting_session):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def after_all_tests(self):
            lcc.log_error("some error")
        
    run_testsuite(MySuite, worker=MyWorker())

    assert reporting_session.get_last_test_outcome() == True
    assert_report_errors(1)
