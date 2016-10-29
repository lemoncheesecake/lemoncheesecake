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

def run_testsuite(suite):
    launcher = Launcher()
    launcher.load_testsuites([suite])
    report_dir = tempfile.mkdtemp()
    try:
        launcher.run_testsuites(Filter(), os.path.join(report_dir, "report"))
    finally:
        shutil.rmtree(report_dir)

def dummy_test_callback(suite):
    pass