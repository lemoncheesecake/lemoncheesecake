'''
Created on Jan 24, 2016

@author: nicolas
'''

import time

from lemoncheesecake.common import LemonCheesecakeInternalError

DEFAULT_STEP = "-"

LOG_LEVEL_DEBUG = "debug"
LOG_LEVEL_INFO = "info"
LOG_LEVEL_WARN = "warn"
LOG_LEVEL_ERROR = "error"

from lemoncheesecake.testresults import *

_runtime = None # singleton

def initialize_runtime(report_dir):
    global _runtime
    _runtime = _Runtime(report_dir)

def get_runtime():
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime

class _RuntimeState:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = None
        
        self.current_testsuite = None
        self.current_test = None
        self.current_step = None
        self._current_test_outcome = True
        
        self.metainfo = { }
    
    def set_current_testsuite(self, testsuite):
        self.testsuite = testsuite
    
    def set_current_test(self, test):
        self.current_test = test
        self._current_test_outcome = True 
    
    def set_current_test_as_failed(self):
        self._current_test_outcome = False
    
    def get_current_test_outcome(self):
        return self._current_test_outcome

class _Runtime:
    def __init__(self, report_dir):
        self.report_dir = report_dir
        self.results = TestResults()
        self.reporting_backends = [ ]
        self.step_lock = False
        self.current_testsuite_result = None
        self.current_test_result = None
        self.current_step_result = None
        self.current_test = None
        self.current_testsuite = None
    
    def init_reporting_backends(self):
        self.for_each_backend(lambda b: b.initialize(self.results, self.report_dir))
    
    def for_each_backend(self, callback):
        for backend in self.reporting_backends:
            callback(backend)
    
    def begin_tests(self):
        self.results.start_time = time.time()
        self.for_each_backend(lambda b: b.begin_tests())
    
    def end_tests(self):
        self.results.end_time = time.time()
        self.for_each_backend(lambda b: b.end_tests())
    
    def begin_testsuite(self, testsuite):
        self.current_testsuite = testsuite
        suite_result = TestSuiteResults(testsuite.id, testsuite.description, self.current_testsuite_result)
        if self.current_testsuite_result:
            self.current_testsuite_result.sub_testsuites.append(suite_result)
        else:
            self.results.testsuites.append(suite_result)
        self.current_testsuite_result = suite_result
        
        self.for_each_backend(lambda b: b.begin_testsuite(testsuite))
    
    def end_testsuite(self):
        self.current_testsuite_result = self.current_testsuite_result.parent
        self.for_each_backend(lambda b: b.end_testsuite(self.current_testsuite))

    def begin_test(self, test):
        self.current_test = test
        self.current_test_result = TestResult(test.id, test.description)
        self.current_testsuite_result.tests.append(self.current_test_result)
        self.for_each_backend(lambda b: b.begin_test(test))
        self.step(DEFAULT_STEP)
            
    def end_test(self):
        if self.current_test_result.outcome == None:
            self.current_test_result.outcome = True
        
        self.for_each_backend(lambda b: b.end_test(self.current_test, self.current_test_result.outcome))
    
    def step(self, description, force_lock=False):
        if self.step_lock and not force_lock:
            return
        
        # remove previous step from results if it was empty
        if self.current_test_result.steps and not self.current_test_result.steps[-1].entries:
            del self.current_test_result.steps[-1]
        
        self.current_step = description
        self.current_step_result = TestStep(description)
        self.current_test_result.steps.append(self.current_step_result)
        
        self.for_each_backend(lambda b: b.set_step(description))
        
    def log(self, level, content):
        self.current_step_result.entries.append(TestLog(level, content))
        self.for_each_backend(lambda b: b.log(level, content))
    
    def debug(self, content):
        self.log(LOG_LEVEL_DEBUG, content)
    
    def info(self, content):
        self.log(LOG_LEVEL_INFO, content)
    
    def warn(self, content):
        self.log(LOG_LEVEL_WARN, content)
    
    def error(self, content):
        self.current_test_result.outcome = False
        self.log(LOG_LEVEL_ERROR, content)
    
    def check(self, description, outcome, details=None):
        self.current_step_result.entries.append(TestCheck(description, outcome, details))
        
        if outcome == False:
            self.current_test_result.outcome = False
        
        self.for_each_backend(lambda b: b.check(description, outcome, details))
        
        return outcome