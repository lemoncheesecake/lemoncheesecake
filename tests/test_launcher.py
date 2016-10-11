'''
Created on Sep 30, 2016

@author: nicolas
'''

import sys
import tempfile
import shutil

import pytest

from lemoncheesecake.launcher import Launcher, Filter
from lemoncheesecake.runtime import get_runtime
import lemoncheesecake as lcc

from helpers import test_backend, run_testsuite

def test_test_success(test_backend):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    assert test_backend.get_last_test_outcome() == True

def test_test_failure(test_backend):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_eq("val", 1, 2)
    
    run_testsuite(MySuite)
    
    assert test_backend.get_last_test_outcome() == False

def test_exception_unexpected(test_backend):
    class MySuite(lcc.TestSuite):
        @lcc.test("First test")
        def first_test(self):
            1 / 0
        
        @lcc.test("Second test")
        def second_test(self):
            pass
    
    run_testsuite(MySuite)
    
    assert test_backend.get_test_outcome("first_test") == False
    assert test_backend.get_test_outcome("second_test") == True

def test_excepion_aborttest(test_backend):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            raise lcc.AbortTest("test error")
    
        @lcc.test("Some other test")
        def someothertest(self):
            pass
        
    run_testsuite(MySuite)
    
    assert test_backend.get_test_outcome("sometest") == False
    assert test_backend.get_test_outcome("someothertest") == True

def test_exception_aborttestsuite(test_backend):
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
    
    assert test_backend.get_test_outcome("sometest") == False
    assert test_backend.get_test_outcome("someothertest") == False
    assert test_backend.get_test_outcome("anothertest") == True

def test_exception_abortalltests(test_backend):
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
    
    assert test_backend.get_test_outcome("sometest") == False
    assert test_backend.get_test_outcome("someothertest") == False
    assert test_backend.get_test_outcome("anothertest") == False

def test_sub_testsuite_inline(test_backend):
    class MyParentSuite(lcc.TestSuite):
        class MyChildSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                pass
    
    run_testsuite(MyParentSuite)
    
    assert test_backend.get_test_outcome("sometest") == True

def test_sub_testsuite_attr(test_backend):
    class MyChildSuite(lcc.TestSuite):
            @lcc.test("Some test")
            def sometest(self):
                pass
    class MyParentSuite(lcc.TestSuite):
        sub_suites = [MyChildSuite]
    
    run_testsuite(MyParentSuite)
    
    assert test_backend.get_test_outcome("sometest") == True

def test_hook_before_test(test_backend):
    class MySuite(lcc.TestSuite):
        def before_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_log() == "hook called"

def test_hook_after_test(test_backend):
    class MySuite(lcc.TestSuite):
        def after_test(self, test_name):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_log() == "hook called"

def test_hook_before_suite(test_backend):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_log() == "hook called"

def test_hook_after_suite(test_backend):
    class MySuite(lcc.TestSuite):
        def after_suite(self):
            lcc.log_info("hook called")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_log() == "hook called"

def test_hook_error_before_test(test_backend):
    class MySuite(lcc.TestSuite):
        def before_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_test_outcome("sometest") == False

def test_hook_error_after_test(test_backend):
    class MySuite(lcc.TestSuite):
        def after_test(self, test_name):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_test_outcome("sometest") == False

def test_hook_error_before_suite(test_backend):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_test_outcome() == False
    assert get_runtime().reporting_data.errors == 1

def test_hook_error_after_suite(test_backend):
    class MySuite(lcc.TestSuite):
        def after_suite(self):
            1 / 0
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    run_testsuite(MySuite)

    assert test_backend.get_last_test_outcome() == True
    assert get_runtime().reporting_data.errors == 1