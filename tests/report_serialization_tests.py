 # -*- coding: utf-8 -*-
 
'''
Created on Nov 18, 2016

@author: nicolas
'''

from __future__ import print_function

import sys

import lemoncheesecake.api as lcc
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.worker import Worker

from helpers import run_testsuite_class, run_testsuite_classes, assert_report, dump_report

def do_test_serialization(suites, backend, tmpdir, worker=None):
    if type(suites) in (list, tuple):
        run_testsuite_classes(suites, worker=worker, backends=[backend])
    else:
        run_testsuite_class(suites, worker=worker, backends=[backend])
    
    report = get_runtime().report
    
    report_filename = tmpdir.join("report").strpath
    backend.save_report(report_filename, report)
    unserialized_report = backend.load_report(report_filename)
    
#     dump_report(unserialized_report)

    assert_report(unserialized_report, report)    

def test_simple_test(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_test_with_all_metadata(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_testsuite_with_all_metadata(backend, tmpdir):
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_unicode(backend, tmpdir):
    @lcc.link("http://foo.bar", u"éééààà")
    @lcc.prop(u"ééé", u"ààà")
    @lcc.tags(u"ééé", u"ààà")
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.link("http://foo.bar", u"éééààà")
        @lcc.prop(u"ééé", u"ààà")
        @lcc.tags(u"ééé", u"ààà")
        @lcc.test(u"Some test ààà")
        def sometest(self):
            lcc.set_step(u"éééààà")
            lcc.check_that(u"éééààà", 1, lcc.equal_to(1))
            lcc.log_info(u"éééààà")
            lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_multiple_testsuites_and_tests(backend, tmpdir):
    @lcc.testsuite("MySuite1")
    class MySuite1:
        @lcc.tags("foo")
        @lcc.test("Some test 1")
        def test_1_1(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))
        
        @lcc.tags("bar")
        @lcc.test("Some test 2")
        def test_1_2(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))
        
        @lcc.tags("baz")
        @lcc.test("Some test 3")
        def test_1_3(self):
            lcc.check_that("foo", 3, lcc.equal_to(2))
    
    @lcc.testsuite("MySuite2")
    class MySuite2:
        @lcc.prop("foo", "bar")
        @lcc.test("Some test 1")
        def test_2_1(self):
            1 / 0
        
        @lcc.prop("foo", "baz")
        @lcc.test("Some test 2")
        def test_2_2(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))
        
        @lcc.test("Some test 3")
        def test_2_3(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))
    
        # suite3 is a sub suite of suite3
        @lcc.testsuite("MySuite3")
        class MySuite3:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))
            
            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                raise lcc.AbortTest()
            
            @lcc.test("Some test 3")
            def test_3_3(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))
    
    do_test_serialization((MySuite1, MySuite2), backend, tmpdir)

def test_check_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("foo"))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_check_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("bar"))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_require_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("foo"))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_require_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("bar"))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_assert_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_that("somevalue", "foo", lcc.equal_to("bar"))
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_all_types_of_logs(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warn("some warning message")
        
        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")

    do_test_serialization(MySuite, backend, tmpdir)

def test_multiple_steps(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_attachment(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.save_attachment_content("foobar", "foobar.txt")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_setup_suite_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_info("some log")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)

def test_setup_suite_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_error("something bad happened")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)

def test_teardown_suite_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")

    do_test_serialization(MySuite, backend, tmpdir)

def test_teardown_suite_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_error("something bad happened")

    do_test_serialization(MySuite, backend, tmpdir)

def test_setup_and_teardown_suite(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass
        
        def setup_suite(self):
            lcc.log_info("some log")

        def teardown_suite(self):
            lcc.log_info("some other log")

    do_test_serialization(MySuite, backend, tmpdir)

def test_setup_test_session_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_info("some log")

    do_test_serialization(MySuite, backend, tmpdir, worker=MyWorker())

def test_setup_test_session_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_error("something bad happened")

    do_test_serialization(MySuite, backend, tmpdir, worker=MyWorker())

def test_teardown_test_session_success(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.log_info("some log")

    do_test_serialization(MySuite, backend, tmpdir, worker=MyWorker())

def test_teardown_test_session_failure(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.log_error("something bad happened")
    
    do_test_serialization(MySuite, backend, tmpdir, worker=MyWorker())

def test_setup_and_teardown_test_session(backend, tmpdir):
    @lcc.testsuite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_info("some log")
            
        def teardown_test_session(self):
            lcc.log_info("some other log")

    do_test_serialization(MySuite, backend, tmpdir, worker=MyWorker())