'''
Created on Sep 30, 2016

@author: nicolas
'''

import os
import sys
import tempfile
import shutil

import pytest

from lemoncheesecake.launcher import Launcher, Filter
from lemoncheesecake import reporting
from lemoncheesecake.runtime import get_runtime

def build_test_module(name="mytestsuite"):
    return """
from lemoncheesecake import *

class {name}(TestSuite):
    @test("This is a test")
    def test_{name}(self):
        pass
""".format(name=name)

class TestBackend(reporting.ReportingBackend):
    def __init__(self):
        self._test_outcomes = {}
        self._last_test_outcome = None
        self._test_nb = 0
        self._last_log = None
        self._last_test = None
    
    def get_last_test(self):
        return self._last_test
    
    def get_last_test_outcome(self):
        return self._last_test_outcome
    
    def get_last_log(self):
        return self._last_log
    
    def get_test_outcome(self, test_id):
        return self._test_outcomes[test_id]
    
    def begin_test(self, test):
        self._last_test_outcome = None
    
    def end_test(self, test, outcome):
        self._last_test = test.id
        self._test_outcomes[test.id] = outcome
        self._last_test_outcome = outcome
        self._test_nb += 1
    
    def log(self, level, content):
        self._last_log = content

def get_test_backend():
    backend = TestBackend()
    reporting.register_backend("test", backend)
    reporting.only_enable_backends(["test"])
    return backend

@pytest.fixture()
def test_backend():
    return get_test_backend()

def run_testsuites(suites):
    launcher = Launcher()
    launcher.load_testsuites(suites)
    report_dir = tempfile.mkdtemp()
    try:
        launcher.run_testsuites(Filter(), os.path.join(report_dir, "report"))
    finally:
        shutil.rmtree(report_dir)

def run_testsuite(suite):
    run_testsuites([suite])

def dummy_test_callback(suite):
    pass

def assert_test_data_from_test(test_data, test):
    assert test_data.id == test.id
    assert test_data.description == test.description
    assert test_data.tags == test.tags
    assert test_data.properties == test.properties
    assert test_data.links == test.links

def assert_testsuite_data_from_testsuite(testsuite_data, testsuite):
    assert testsuite_data.id == testsuite.id
    assert testsuite_data.description == testsuite.description
    assert testsuite_data.tags == testsuite.tags
    assert testsuite_data.properties == testsuite.properties
    assert testsuite_data.links == testsuite.links
    assert len(testsuite_data.tests) == len(testsuite.get_tests())
    
    assert len(testsuite_data.tests) == len(testsuite.get_tests())
    for test_data, test in zip(testsuite_data.tests, testsuite.get_tests()):
        assert_test_data_from_test(test_data, test)
    
    assert len(testsuite_data.sub_testsuites) == len(testsuite.get_sub_testsuites())
    for sub_testsuite_data, sub_testsuite in zip(testsuite_data.sub_testsuites, testsuite.get_sub_testsuites()):
        assert_testsuite_data_from_testsuite(sub_testsuite_data, sub_testsuite)
    
def assert_report_from_testsuites(report, suite_classes):
    assert len(report.testsuites) == len(suite_classes)
    for testsuite_data, testsuite_class in zip(report.testsuites, suite_classes):
        testsuite = testsuite_class()
        testsuite.load()
        assert_testsuite_data_from_testsuite(testsuite_data, testsuite)

def assert_report_from_testsuite(report, suite_class):
    assert_report_from_testsuites(report, [suite_class])
    