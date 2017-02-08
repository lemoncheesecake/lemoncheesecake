 # -*- coding: utf-8 -*-

'''
Created on Nov 1, 2016

@author: nicolas
'''

import sys
import os.path
import tempfile

import pytest

from lemoncheesecake.exceptions import *
import lemoncheesecake as lcc
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.worker import Worker
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string
from lemoncheesecake.reporting.backends.json_ import serialize_report

from helpers import run_testsuite, run_testsuites, assert_report_from_testsuite, assert_report_from_testsuites, assert_report_stats, \
    dump_report

def test_simple_test():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)
    
    assert report.get_test("sometest").outcome == True

def test_test_with_all_metadata():
    class MySuite(lcc.TestSuite):
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    assert report.get_test("sometest").outcome == True

def test_testsuite_with_all_metadata():
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_int_eq("foo", 1, 1)
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)
    
    assert report.get_test("sometest").outcome == True

def test_multiple_testsuites_and_tests():
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
                raise lcc.AbortTest("error")
            
            @lcc.test("Some test 3")
            def test_3_3(self):
                lcc.check_int_eq("foo", 1, 1)
    
    run_testsuites([MySuite1, MySuite2])
    
    report = get_runtime().report

    assert_report_from_testsuites(report, [MySuite1, MySuite2])
    assert_report_stats(
        report,
        expected_test_successes=6, expected_test_failures=3,
        expected_check_successes=6, expected_check_failures=1, expected_error_logs=2
    )
    
    assert report.get_test("test_1_1").outcome == True
    assert report.get_test("test_1_2").outcome == True
    assert report.get_test("test_1_3").outcome == False

    assert report.get_test("test_2_1").outcome == False
    assert report.get_test("test_2_2").outcome == True
    assert report.get_test("test_2_3").outcome == True

    assert report.get_test("test_3_1").outcome == True
    assert report.get_test("test_3_2").outcome == False
    assert report.get_test("test_3_3").outcome == True
    
def test_check_success():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_eq("somevalue", "foo", "foo")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)
    
    test = report.get_test("test_1")
    assert test.outcome == True
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome == True
    assert step.entries[0].details == None

def test_check_failure():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_eq("somevalue", "foo", "bar")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_failures=1, expected_check_failures=1)
    
    test = report.get_test("test_1")
    assert test.outcome == False
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome == False
    assert "foo" in step.entries[0].details

def test_assert_success():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_eq("somevalue", "foo", "foo")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)
    
    test = report.get_test("test_1")
    assert test.outcome == True
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome == True
    assert step.entries[0].details == None

def test_assert_failure():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_eq("somevalue", "foo", "bar")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_failures=1, expected_check_failures=1, expected_error_logs=1)
    
    test = report.get_test("test_1")
    assert test.outcome == False
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome == False
    assert "foo" in step.entries[0].details

def test_all_types_of_logs():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warn("some warning message")
        
        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, 
        expected_test_successes=1, expected_test_failures=1, 
        expected_error_logs=1, expected_warning_logs=1
    )
    
    test = report.get_test("test_1")
    assert test.outcome == True
    step = test.steps[0]
    assert step.entries[0].level == "debug"
    assert step.entries[0].message == "some debug message"
    assert step.entries[1].level == "info"
    assert step.entries[1].message == "some info message"
    assert step.entries[2].level == "warn"
    
    test = report.get_test("test_2")
    assert test.outcome == False
    step = test.steps[0]    
    assert step.entries[0].message == "some error message"
    assert step.entries[0].level == "error"

def test_multiple_steps():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)

    test = report.get_test("sometest")
    assert test.outcome == True
    assert test.steps[0].description == "step 1"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"
    assert test.steps[1].description == "step 2"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something else"

def test_default_step():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    test = report.get_test("sometest")
    assert test.outcome == True
    assert test.steps[0].description == "Some test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"

def test_step_after_test_setup():
    class MySuite(lcc.TestSuite):
        def setup_test(self, test_name):
            lcc.log_info("in test setup")
        
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    test = report.get_test("sometest")
    assert test.outcome == True
    assert test.steps[0].description == "Setup test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "in test setup"
    assert test.steps[1].description == "Some test"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something"

def test_prepare_attachment(tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            filename = lcc.prepare_attachment("foobar.txt", "some description")
            with open(filename, "w") as fh:
                fh.write("some content")
    
    run_testsuite(MySuite, tmpdir=tmpdir)
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)

    test = report.get_test("sometest")
    assert test.steps[0].entries[0].filename.endswith("foobar.txt")
    assert test.steps[0].entries[0].description == "some description"
    assert test.outcome == True
    assert open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename)).read() == "some content"

def test_save_attachment_file(tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, "somefile.txt")
            with open(filename, "w") as fh:
                fh.write("some other content")
            lcc.save_attachment_file(filename, "some other file")
    
    run_testsuite(MySuite, tmpdir=tmpdir)
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)

    test = report.get_test("sometest")
    assert test.steps[0].entries[0].filename.endswith("somefile.txt")
    assert test.steps[0].entries[0].description == "some other file"
    assert test.outcome == True
    assert open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename)).read() == "some other content"

def _test_save_attachment_content(tmpdir, file_name, file_content, encoding=None):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.save_attachment_content(file_content, file_name, binary_mode=not encoding)
    
    run_testsuite(MySuite, tmpdir=tmpdir)
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)

    test = report.get_test("sometest")
    assert test.steps[0].entries[0].filename.endswith(file_name)
    assert test.steps[0].entries[0].description == file_name
    assert test.outcome == True
    fh = open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename), "rb")
    actual_content = fh.read()
    if encoding != None:
        actual_content = actual_content.decode(encoding)
    assert actual_content == file_content

def test_save_attachment_text_ascii(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", "foobar", encoding="ascii")

def test_save_attachment_text_utf8(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", u"éééçççààà", encoding="utf-8")

def test_save_attachment_binary(tmpdir):
    p = os.path
    content = open(p.join(p.dirname(__file__), p.pardir, "misc", "report-screenshot.png"), "rb").read()
    _test_save_attachment_content(tmpdir, "foobar.png", content)

def test_unicode(tmpdir):
    class MySuite(lcc.TestSuite):
        @lcc.test("some test")
        def sometest(self):
            lcc.set_step(u"éééààà")
            lcc.check_int_eq(u"éééààà", 1, 1)
            lcc.log_info(u"éééààà")
            lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")
    
    run_testsuite(MySuite, tmpdir=tmpdir)
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    test = report.get_test("sometest")
    assert test.outcome == True
    step = test.steps[0]
    assert step.description == u"éééààà"
    assert u"éééààà" in step.entries[0].description
    assert "1" in step.entries[0].description
    assert step.entries[1].message == u"éééààà"
    assert step.entries[2].filename.endswith(u"somefileààà")
    assert step.entries[2].description == u"éééààà"
    assert open(os.path.join(get_runtime().report_dir, step.entries[2].filename)).read() == "A" * 1024

def test_setup_suite_success():
    class MySuite(lcc.TestSuite):
        def setup_suite(self):
            lcc.log_info("some log")
        
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    suite = report.get_suite("MySuite")
    assert suite.suite_setup.outcome == True
    assert suite.suite_setup.start_time != None
    assert suite.suite_setup.end_time != None
    assert suite.suite_setup.steps[0].entries[0].message == "some log"
    assert suite.suite_setup.has_failure() == False
    assert report.get_test("sometest").outcome == True

def test_setup_suite_failure():
    class MySuite(lcc.TestSuite):
        def setup_suite(self):
            lcc.log_error("something bad happened")
        
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_failures=1, expected_errors=1, expected_error_logs=2)
    
    suite = report.get_suite("MySuite")
    assert suite.suite_setup.outcome == False
    assert suite.suite_setup.start_time != None
    assert suite.suite_setup.end_time != None
    assert suite.suite_setup.steps[0].entries[0].message == "something bad happened"
    assert suite.suite_setup.has_failure() == True
    assert report.get_test("sometest").outcome == False

def test_setup_suite_without_content():
    marker = []
    
    class MySuite(lcc.TestSuite):
        def setup_suite(self):
            marker.append("setup")
        
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    run_testsuite(MySuite)
    
    report = get_runtime().report
    
    assert report.testsuites[0].suite_setup == None
    assert marker == ["setup"]

def test_teardown_suite_success():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    suite = report.get_suite("MySuite")
    assert suite.suite_teardown.outcome == True
    assert suite.suite_teardown.start_time != None
    assert suite.suite_teardown.end_time != None
    assert suite.suite_teardown.steps[0].entries[0].message == "some log"
    assert suite.suite_teardown.has_failure() == False
    assert report.get_test("sometest").outcome == True

def test_teardown_suite_failure():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.check_eq("val", 1, 2)
        
    run_testsuite(MySuite)
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_errors=1, expected_check_failures=1)
    
    suite = report.get_suite("MySuite")
    assert suite.suite_teardown.outcome == False
    assert suite.suite_teardown.start_time != None
    assert suite.suite_teardown.end_time != None
    assert suite.suite_teardown.steps[0].entries[0].outcome == False
    assert suite.suite_teardown.has_failure() == True
    assert report.get_test("sometest").outcome == True

def test_teardown_suite_without_content():
    marker = []
    
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            marker.append("teardown")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report
    
    assert report.testsuites[0].suite_teardown == None
    assert marker == ["teardown"]

def test_setup_test_session_success():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_info("some log")
    
    run_testsuite(MySuite, worker=MyWorker())
    
    report = get_runtime().report

    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    assert report.test_session_setup.outcome == True
    assert report.test_session_setup.start_time != None
    assert report.test_session_setup.end_time != None
    assert report.test_session_setup.steps[0].entries[0].message == "some log"
    assert report.test_session_setup.has_failure() == False
    assert report.get_test("sometest").outcome == True

def test_setup_test_session_failure():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def setup_test_session(self):
            lcc.log_error("something bad happened")
    
    run_testsuite(MySuite, worker=MyWorker())
    
    report = get_runtime().report
    
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_failures=1, expected_errors=1, expected_error_logs=2)
    
    assert report.test_session_setup.outcome == False
    assert report.test_session_setup.start_time != None
    assert report.test_session_setup.end_time != None
    assert report.test_session_setup.steps[0].entries[0].message == "something bad happened"
    assert report.test_session_setup.has_failure() == True
    assert report.get_test("sometest").outcome == False
 
def test_setup_test_session_without_content():
    marker = []
    
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def setup_test_session(self):
            marker.append("setup")
     
    run_testsuite(MySuite, worker=MyWorker())

    report = get_runtime().report
    
    assert report.test_session_setup == None
    assert marker == ["setup"]
 
def test_teardown_test_session_success():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.log_info("some log")
    
    run_testsuite(MySuite, worker=MyWorker())
    
    report = get_runtime().report
 
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1)
    
    assert report.test_session_teardown.outcome == True
    assert report.test_session_teardown.start_time != None
    assert report.test_session_teardown.end_time != None
    assert report.test_session_teardown.steps[0].entries[0].message == "some log"
    assert report.test_session_teardown.has_failure() == False
    assert report.get_test("sometest").outcome == True
 
def test_teardown_test_session_failure():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def teardown_test_session(self):
            lcc.check_eq("val", 1, 2)
    
    run_testsuite(MySuite, worker=MyWorker())
         
    report = get_runtime().report
     
    assert_report_from_testsuite(report, MySuite)
    assert_report_stats(report, expected_test_successes=1, expected_errors=1, expected_check_failures=1)
    
    assert report.test_session_teardown.outcome == False
    assert report.test_session_teardown.start_time != None
    assert report.test_session_teardown.end_time != None
    assert report.test_session_teardown.steps[0].entries[0].outcome == False
    assert report.test_session_teardown.has_failure() == True
    assert report.get_test("sometest").outcome == True

def test_teardown_test_session_without_content():
    marker = []
    
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    class MyWorker(Worker):
        def teardown_test_session(self):
            marker.append("teardown")

    run_testsuite(MySuite, worker=MyWorker())

    report = get_runtime().report
    
    assert report.test_session_teardown == None
    assert marker == ["teardown"]

def add_report_info():
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            lcc.add_report_info("some info", "some data")
    
    run_testsuite(MySuite)
    
    report = get_runtime().report
    
    assert report.info[-1] == ["some info", "some data"]