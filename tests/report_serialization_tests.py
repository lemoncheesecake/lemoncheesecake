 # -*- coding: utf-8 -*-
 
'''
Created on Nov 18, 2016

@author: nicolas
'''

import sys

import lemoncheesecake as lcc
from lemoncheesecake.runtime import get_runtime

from helpers import run_testsuite, run_testsuites, assert_report

def do_test_serialization(suites, backend, tmpdir):
    if type(suites) in (list, tuple):
        run_testsuites(suites)
    else:
        run_testsuite(suites)
    
    report = get_runtime().report
        
    backend.serialize_report(report, tmpdir.strpath)
#     print >> sys.stderr, open(tmpdir.strpath + "/report.xml").read()
    unserialized_report = backend.unserialize_report(tmpdir.strpath)
    
    assert_report(unserialized_report, report)    

def test_simple_test(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_test_with_all_metadata(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_testsuite_with_all_metadata(backend, tmpdir):
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_unicode(backend, tmpdir):
    @lcc.link("http://foo.bar", u"éééààà")
    @lcc.prop(u"ééé", u"ààà")
    @lcc.tags(u"ééé", u"ààà")
    @lcc.test(u"Some test ààà")
    def sometest(self):
        lcc.set_step(u"éééààà")
        lcc.check_int_eq(u"éééààà", 1, 1)
        lcc.log_info(u"éééààà")
        lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")

def test_multiple_testsuites_and_tests(backend, tmpdir):
    class MySuite1(lcc.TestSuite):
        @lcc.tags("foo")
        @lcc.test("Some test 1")
        def test_1_1(self):
            lcc.check_int_eq("foo", 2, 2)
        
        @lcc.tags("bar")
        @lcc.test("Some test 2")
        def test_1_2(self):
            lcc.check_int_eq("foo", 2, 2)
        
        @lcc.tags("baz")
        @lcc.test("Some test 3")
        def test_1_3(self):
            lcc.check_int_eq("foo", 3, 2)
    
    class MySuite2(lcc.TestSuite):
        @lcc.prop("foo", "bar")
        @lcc.test("Some test 1")
        def test_2_1(self):
            1 / 0
        
        @lcc.prop("foo", "baz")
        @lcc.test("Some test 2")
        def test_2_2(self):
            lcc.check_int_eq("foo", 2, 2)
        
        @lcc.test("Some test 3")
        def test_2_3(self):
            lcc.check_int_eq("foo", 2, 2)
    
        # suite3 is a sub suite of suite3
        class MySuite3(lcc.TestSuite):
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                lcc.check_int_eq("foo", 1, 1)
            
            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                raise lcc.AbortTest()
            
            @lcc.test("Some test 3")
            def test_3_3(self):
                lcc.check_int_eq("foo", 1, 1)
    
    do_test_serialization((MySuite1, MySuite2), backend, tmpdir)

def test_check_success(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_eq("somevalue", "foo", "foo")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_check_failure(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_eq("somevalue", "foo", "bar")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_assert_success(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_eq("somevalue", "foo", "foo")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_assert_failure(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_eq("somevalue", "foo", "bar")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_all_types_of_logs(backend, tmpdir):
    class MySuite(lcc.TestSuite):
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
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_attachment(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.save_attachment_content("foobar", "foobar.txt")
    
    do_test_serialization(MySuite, backend, tmpdir)

def test_before_suite_success(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            lcc.log_info("some log")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)

def test_before_suite_failure(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        def before_suite(self):
            lcc.log_error("something bad happened")
        
        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)

def test_after_suite_success(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def after_suite(self):
            lcc.log_info("some log")

    do_test_serialization(MySuite, backend, tmpdir)

def test_after_suite_failure(backend, tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def after_suite(self):
            lcc.log_error("something bad happened")

    do_test_serialization(MySuite, backend, tmpdir)