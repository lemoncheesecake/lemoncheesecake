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

_runtime = None # singleton

def initialize_runtime(report_dir):
    _runtime = _Runtime(report_dir)

def get_runtime():
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime

class _RuntimeState:
    def __init__(self):
        self.tests = 0
        self.tests_success = 0
        self.tests_failure = 0
        self.checks = 0
        self.checks_success = 0
        self.checks_failure = 0
        self.errors = 0
        self.warnings = 0
        
        self.start_time = None
        self.end_time = None
        
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
        self.state = _RuntimeState()
        self.reporting_backends = [ ]
        self.step_lock = False
    
    def for_each_backend(self, callback):
        for backend in self.reporting_backends:
            callback(backend)
    
    def begin_tests(self):
        self.state.start_time = time.time()
        for backend in self.reporting_backends:
            backend.begin_tests()
    
    def end_tests(self):
        self.state.end_time = time.time()
        self.for_each_backend(lambda b: b.end_tests())
    
    def begin_testsuite(self, testsuite):
        self.state.current_testsuite = testsuite
        self.for_each_backend(lambda b: b.begin_testsuite(testsuite))
    
    def end_testsuite(self):
        self.for_each_backend(lambda b: b.end_testsuite())

    def begin_test(self, test):
        self.state.set_current_test(test)
        self.for_each_backend(lambda b: b.begin_test(test))
        self.for_each_backend(lambda b: b.set_step(DEFAULT_STEP))
            
    def end_test(self):
        if self.state.current_test_outcome:
            self.state.tests_success += 1
        else:
            self.state.tests_failure += 1
        
        self.for_each_backend(lambda b: b.end_test(self.state_current_test_outcome))
    
    def step(self, description, force_lock=False):
        if self.step_lock and not force_lock:
            return
        
        self.state.current_step = description
        
        self.for_each_backend(lambda b: b.set_step(description))
        
    def log(self, level, content):
        self.for_each_backend(lambda b: b.log(level, content))
    
    def debug(self, content):
        self.log(LOG_LEVEL_DEBUG, content)
    
    def info(self, content):
        self.log(LOG_LEVEL_INFO, content)
    
    def warn(self, content):
        self.state.warnings += 1
        self.log(LOG_LEVEL_WARN, content)
    
    def error(self, content):
        self.state.errors += 1
        self.state.set_current_test_as_failed()
        self.log(LOG_LEVEL_ERROR, content)
    
    def check(self, description, outcome, details=None):
        self.state.checks += 1
        if outcome:
            self.state.checks_success += 1
        else:
            self.state.checks_failure += 1
            self.state.set_current_test_as_failed()
        
        self.for_each_backend(lambda b: b.check(description, outcome, details))
        
        return outcome