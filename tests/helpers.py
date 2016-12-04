'''
Created on Sep 30, 2016

@author: nicolas
'''

from __future__ import print_function

import os
import sys
import tempfile
import shutil

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.launcher import Launcher, Filter
from lemoncheesecake import reporting
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.workers import add_worker, clear_workers
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string

def build_test_module(name="mytestsuite"):
    return """
from lemoncheesecake import *

class {name}(TestSuite):
    @test("This is a test")
    def test_{name}(self):
        pass
""".format(name=name)

class ReportingSession(reporting.ReportingSession):
    def __init__(self):
        self._test_outcomes = {}
        self._last_test_outcome = None
        self._test_nb = 0
        self._last_log = None
        self._last_test = None
        self._last_check_description = None
        self._last_check_outcome = None
        self._last_check_details = None
        self._error_log_nb = 0
    
    def get_last_test(self):
        return self._last_test
    
    def get_last_test_outcome(self):
        return self._last_test_outcome
    
    def get_last_log(self):
        return self._last_log
    
    def get_error_log_nb(self):
        return self._error_log_nb
    
    def get_test_outcome(self, test_id):
        return self._test_outcomes[test_id]
    
    def get_last_check(self):
        return self._last_check_description, self._last_check_outcome, self._last_check_details
    
    def begin_test(self, test):
        self._last_test_outcome = None
    
    def end_test(self, test, outcome):
        self._last_test = test.id
        self._test_outcomes[test.id] = outcome
        self._last_test_outcome = outcome
        self._test_nb += 1
    
    def log(self, level, content):
        if level == "error":
            self._error_log_nb += 1
        self._last_log = content
    
    def check(self, description, outcome, details=None):
        self._last_check_description = description
        self._last_check_outcome = outcome
        self._last_check_details = details

def get_reporting_session():
    class ReportingBackend(reporting.ReportingBackend):
        name = "test_backend"
        
        def __init__(self, reporting_session):
            self.reporting_session = reporting_session
        
        def create_reporting_session(self, report, report_dir):
            return self.reporting_session

    reporting_session = ReportingSession()
    backend = ReportingBackend(reporting_session)
    reporting.register_backend("test", backend)
    reporting.set_enabled_backends(["test"])
    return reporting_session

@pytest.fixture()
def reporting_session():
    return get_reporting_session()

def run_testsuites(suites, worker=None, tmpdir=None):
    launcher = Launcher()
    launcher.load_testsuites(suites)
    
    clear_workers()
    if worker:
        add_worker("testworker", worker)
    
    if tmpdir:
        launcher.run_testsuites(Filter(), os.path.join(tmpdir.strpath, "report"))
    else:
        report_dir = tempfile.mkdtemp()
        try:
            launcher.run_testsuites(Filter(), os.path.join(report_dir, "report"))
        finally:
            shutil.rmtree(report_dir)
    
    dump_report(get_runtime().report)

def run_testsuite(suite, worker=None, tmpdir=None):
    run_testsuites([suite], worker=worker, tmpdir=tmpdir)

def run_func_in_test(callback):
    class MySuite(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            callback()
    
    run_testsuite(MySuite)

def dump_report(report):
    xml = serialize_report_as_string(report)
    print(xml, file=sys.stderr)

def dummy_test_callback(suite):
    pass

def assert_check_data(actual, expected):
    assert actual.description == expected.description
    assert actual.outcome == expected.outcome
    assert actual.details == expected.details

def assert_log_data(actual, expected):
    assert actual.level == expected.level
    assert actual.message == expected.message

def assert_attachment_data(actual, expected):
    assert actual.description == expected.description
    assert actual.filename == expected.filename

def assert_step_data(actual, expected):
    assert actual.start_time == expected.start_time
    assert actual.end_time == expected.end_time
    assert actual.description == expected.description
    assert len(actual.entries) == len(expected.entries)
    for actual_entry, expected_entry in zip(actual.entries, expected.entries):
        assert actual_entry.__class__ == expected_entry.__class__
        if isinstance(actual_entry, reporting.LogData):
            assert_log_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.CheckData):
            assert_check_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.AttachmentData):
            assert_attachment_data(actual_entry, expected_entry)
        else:
            raise Exception("Unknown class '%s'" % actual.__class__.__name__)

def assert_test_data(actual, expected):
    assert actual.id == expected.id
    assert actual.description == expected.description
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links
    assert actual.outcome == expected.outcome
    assert actual.start_time == expected.start_time
    assert actual.end_time == expected.end_time
    
    assert len(actual.steps) == len(expected.steps)
    for actual_step, expected_step in zip(actual.steps, expected.steps):
        assert_step_data(actual_step, expected_step)

def assert_hook_data(actual, expected):
    if expected == None:
        assert actual == None
    else:
        assert actual.start_time == expected.start_time
        assert actual.end_time == expected.end_time
        assert len(actual.steps) == len(expected.steps)
        for actual_step, expected_step in zip(actual.steps, expected.steps):
            assert_step_data(actual_step, expected_step)

def assert_testsuite_data(actual, expected):
    assert actual.id == expected.id
    assert actual.description == expected.description
    if expected.parent == None:
        assert actual.parent == None
    else:
        assert actual.parent.id == expected.parent.id
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links
    
    assert_hook_data(actual.before_suite, expected.before_suite)
    
    assert len(actual.tests) == len(expected.tests)
    for actual_test, expected_test in zip(actual.tests, expected.tests):
        assert_test_data(actual_test, expected_test)
    
    assert len(actual.sub_testsuites) == len(expected.sub_testsuites)
    for actual_subsuite, expected_subsuite in zip(actual.sub_testsuites, expected.sub_testsuites):
        assert_testsuite_data(actual_subsuite, expected_subsuite)

    assert_hook_data(actual.after_suite, expected.after_suite)

def assert_report(actual, expected):
    assert actual.info == expected.info
    assert actual.start_time == expected.start_time
    assert actual.end_time == expected.end_time
    assert actual.report_generation_time == expected.report_generation_time
    assert len(actual.testsuites) == len(expected.testsuites)
    
    assert_hook_data(actual.before_all_tests, expected.before_all_tests)
    
    for actual_testsuite, expected_testsuite in zip(actual.testsuites, expected.testsuites):
        assert_testsuite_data(actual_testsuite, expected_testsuite)

    assert_hook_data(actual.after_all_tests, expected.after_all_tests)

def assert_steps_data(steps):
    for step in steps:
        assert step.start_time
        assert step.end_time >= step.start_time

def assert_test_data_from_test(test_data, test):
    assert test_data.id == test.id
    assert test_data.description == test.description
    assert test_data.tags == test.tags
    assert test_data.properties == test.properties
    assert test_data.links == test.links
    
    assert_steps_data(test_data.steps)

def assert_testsuite_data_from_testsuite(testsuite_data, testsuite):
    assert testsuite_data.id == testsuite.id
    assert testsuite_data.description == testsuite.description
    assert testsuite_data.tags == testsuite.tags
    assert testsuite_data.properties == testsuite.properties
    assert testsuite_data.links == testsuite.links
    
    if testsuite.has_hook("before_suite"):
        assert testsuite_data.before_suite != None
        assert testsuite_data.before_suite.start_time != None
        assert testsuite_data.before_suite.end_time != None
        assert_steps_data(testsuite_data.before_suite.steps)
    
    assert len(testsuite_data.tests) == len(testsuite.get_tests())
    for test_data, test in zip(testsuite_data.tests, testsuite.get_tests()):
        assert_test_data_from_test(test_data, test)
    
    assert len(testsuite_data.sub_testsuites) == len(testsuite.get_sub_testsuites())
    for sub_testsuite_data, sub_testsuite in zip(testsuite_data.sub_testsuites, testsuite.get_sub_testsuites()):
        assert_testsuite_data_from_testsuite(sub_testsuite_data, sub_testsuite)

    if testsuite.has_hook("after_suite"):
        assert testsuite_data.after_suite != None
        assert testsuite_data.after_suite.start_time != None
        assert testsuite_data.after_suite.end_time != None
        assert_steps_data(testsuite_data.after_suite.steps)
    
def assert_report_from_testsuites(report, suite_classes):
    assert report.start_time != None
    assert report.end_time != None
    assert report.report_generation_time != None
    assert len(report.testsuites) == len(suite_classes)
    for testsuite_data, testsuite_class in zip(report.testsuites, suite_classes):
        testsuite = testsuite_class()
        testsuite.load()
        assert_testsuite_data_from_testsuite(testsuite_data, testsuite)

def assert_report_from_testsuite(report, suite_class):
    assert_report_from_testsuites(report, [suite_class])

def assert_report_stats(report,
                        expected_test_successes=0, expected_test_failures=0, expected_errors=0,
                        expected_check_successes=0, expected_check_failures=0,
                        expected_error_logs=0, expected_warning_logs=0):
    stats = report.get_stats()
    assert stats.tests == expected_test_successes + expected_test_failures
    assert stats.test_successes == expected_test_successes
    assert stats.test_failures == expected_test_failures
    assert stats.errors == expected_errors
    assert stats.checks == expected_check_successes + expected_check_failures
    assert stats.check_successes == expected_check_successes
    assert stats.check_failures == expected_check_failures
    assert stats.error_logs == expected_error_logs
    assert stats.warning_logs == expected_warning_logs