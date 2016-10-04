'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake import reporting

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
        self._last_test_outcome = None
    
    def get_last_test_outcome(self):
        return self._last_test_outcome
    
    def begin_test(self, test):
        self._last_test_outcome = None
    
    def end_test(self, test, outcome):
        self._last_test_outcome = outcome

@pytest.fixture()
def test_backend():
    backend = TestBackend()
    reporting.register_backend("test", backend)
    reporting.only_enable_backends(backend)
    return backend