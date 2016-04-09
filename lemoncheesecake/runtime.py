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

from lemoncheesecake.reportingdata import *

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
        self.reporting_data = None
        
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
        self.reporting_data = ReportingData()
        self.report_backends = [ ]
        self.step_lock = False
        # pointers to reporting data parts
        self.current_testsuite_data = None
        self.current_test_data = None
        self.current_step_data = None
        self.current_step_data_list = None
        # pointers to running test/testsuite
        self.current_test = None
        self.current_testsuite = None
    
    def init_reporting_backends(self):
        self.for_each_backend(lambda b: b.initialize(self.reporting_data, self.report_dir))
    
    def for_each_backend(self, callback):
        for backend in self.report_backends:
            callback(backend)
    
    def begin_tests(self):
        self.reporting_data.start_time = time.time()
        self.for_each_backend(lambda b: b.begin_tests())
    
    def end_tests(self):
        self.reporting_data.end_time = time.time()
        self.reporting_data.report_generation_time = self.reporting_data.end_time
        self.for_each_backend(lambda b: b.end_tests())
    
    def begin_before_suite(self, testsuite):        
        self.current_testsuite = testsuite
        suite_data = TestSuiteData(testsuite.id, testsuite.description, self.current_testsuite_data)
        suite_data.before_suite_start_time = time.time()
        if self.current_testsuite_data:
            self.current_testsuite_data.sub_testsuites.append(suite_data)
        else:
            self.reporting_data.testsuites.append(suite_data)
        self.current_testsuite_data = suite_data
        self.current_step_data_list = self.current_testsuite_data.before_suite_steps

        self.for_each_backend(lambda b: b.begin_before_suite(testsuite))

        self.step(DEFAULT_STEP)
    
    def end_before_suite(self):
        self.current_testsuite_data.before_suite_end_time = time.time()
        self.for_each_backend(lambda b: b.end_before_suite(self.current_testsuite))
        
    def begin_after_suite(self, testsuite):
        self.current_testsuite_data.after_suite_start_time = time.time()
        self.current_step_data_list = self.current_testsuite_data.after_suite_steps
        self.for_each_backend(lambda b: b.begin_after_suite(testsuite))

        self.step(DEFAULT_STEP)

    def end_after_suite(self):
        self.current_testsuite_data.after_suite_end_time = time.time()
        self.current_testsuite_data = self.current_testsuite_data.parent
        self.for_each_backend(lambda b: b.end_after_suite(self.current_testsuite))
        self.current_testsuite = None
        
    def begin_test(self, test):
        self.current_test = test
        self.current_test_data = TestData(test.id, test.description)
        self.current_test_data.start_time = time.time()
        self.current_testsuite_data.tests.append(self.current_test_data)
        self.for_each_backend(lambda b: b.begin_test(test))
        self.current_step_data_list = self.current_test_data.steps
        self.step(DEFAULT_STEP)
            
    def end_test(self):
        if self.current_test_data.outcome == None:
            self.current_test_data.outcome = True
        self.current_test_data.end_time = time.time()
        
        self.for_each_backend(lambda b: b.end_test(self.current_test, self.current_test_data.outcome))

        self.current_test = None
        self.current_test_data = None

    def step(self, description, force_lock=False):
        if self.step_lock and not force_lock:
            return

        self.current_step = description
        self.current_step_data = StepData(description)

        # remove previous step from reporting data if it was empty
        if self.current_step_data_list and not self.current_step_data_list[-1].entries:
            del self.current_step_data_list[-1]
        self.current_step_data_list.append(self.current_step_data)

        self.for_each_backend(lambda b: b.set_step(description))
        
    def log(self, level, content):
        self.current_step_data.entries.append(LogData(level, content))
        self.for_each_backend(lambda b: b.log(level, content))
    
    def debug(self, content):
        self.log(LOG_LEVEL_DEBUG, content)
    
    def info(self, content):
        self.log(LOG_LEVEL_INFO, content)
    
    def warn(self, content):
        self.log(LOG_LEVEL_WARN, content)
    
    def error(self, content):
        if self.current_test_data:
            self.current_test_data.outcome = False
        self.log(LOG_LEVEL_ERROR, content)
    
    def check(self, description, outcome, details=None):
        if not self.current_test:
            raise LemonCheesecakeInternalError("A check can only be associated to a test not a test suite")
        
        self.current_step_data.entries.append(CheckData(description, outcome, details))
        
        if outcome == False:
            self.current_test_data.outcome = False
        
        self.for_each_backend(lambda b: b.check(description, outcome, details))
        
        return outcome