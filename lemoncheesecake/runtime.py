'''
Created on Jan 24, 2016

@author: nicolas
'''

import os.path
import time
import shutil

from lemoncheesecake.utils import humanize_duration
from lemoncheesecake.exceptions import LemonCheesecakeInternalError
from lemoncheesecake.consts import ATTACHEMENT_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import *

__all__ = "log_debug", "log_info", "log_warn", "log_warning", "log_error", "set_step", \
    "prepare_attachment", "save_attachment_file", "save_attachment_content"

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

        self.report = None
        
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
        self.attachments_dir = os.path.join(self.report_dir, ATTACHEMENT_DIR)
        self.attachment_count = 0
        self.report = Report()
        self.reporting_sessions = []
        self.step_lock = False
        self.default_step_description = "-"
        # pointers to report data parts
        self.current_testsuite_data = None
        self.current_test_data = None
        self.current_step_data = None
        self.current_step_data_list = None
        # pointers to running test/testsuite
        self.current_test = None
        self.current_testsuite = None
    
    def initialize_reporting_sessions(self):
        for backend in get_backends():
            session = backend.create_reporting_session(self.report, self.report_dir)
            self.reporting_sessions.append(session)
            
    def for_each_reporting_sessions(self, callback):
        for session in self.reporting_sessions:
            callback(session)
    
    def begin_tests(self):
        self.report.start_time = time.time()
        self.for_each_reporting_sessions(lambda b: b.begin_tests())
    
    def end_tests(self):
        self.report.end_time = time.time()
        self.report.report_generation_time = self.report.end_time
        self.for_each_reporting_sessions(lambda b: b.end_tests())
    
    def begin_before_suite(self, testsuite):
        self.current_testsuite = testsuite
        suite_data = TestSuiteData(testsuite.id, testsuite.description, self.current_testsuite_data)
        suite_data.tags.extend(testsuite.tags)
        suite_data.properties.update(testsuite.properties)
        suite_data.links.extend(testsuite.links)
        if self.current_testsuite_data:
            self.current_testsuite_data.sub_testsuites.append(suite_data)
        else:
            self.report.testsuites.append(suite_data)
        self.current_testsuite_data = suite_data
        self.current_step_data_list = self.current_testsuite_data.before_suite_steps

        if testsuite.has_hook("before_testsuite"):
            suite_data.before_suite_start_time = time.time()

        self.for_each_reporting_sessions(lambda b: b.begin_before_suite(testsuite))
    
    def end_before_suite(self):
        if self.current_testsuite_data.before_suite_start_time:
            self.current_testsuite_data.before_suite_end_time = time.time()
        self.for_each_reporting_sessions(lambda b: b.end_before_suite(self.current_testsuite))
        
    def begin_after_suite(self, testsuite):
        if testsuite.has_hook("after_suite"):
            self.current_testsuite_data.after_suite_start_time = time.time()
        self.current_step_data_list = self.current_testsuite_data.after_suite_steps
        self.for_each_reporting_sessions(lambda b: b.begin_after_suite(testsuite))

    def end_after_suite(self):
        if self.current_testsuite_data.after_suite_start_time:
            self.current_testsuite_data.after_suite_end_time = time.time()
        self.current_testsuite_data = self.current_testsuite_data.parent
        self.for_each_reporting_sessions(lambda b: b.end_after_suite(self.current_testsuite))
        self.current_testsuite = None
        
    def begin_test(self, test):
        self.current_test = test
        self.current_test_data = TestData(test.id, test.description)
        self.current_test_data.tags.extend(test.tags)
        self.current_test_data.properties.update(test.properties)
        self.current_test_data.links.extend(test.links)
        self.current_test_data.start_time = time.time()
        self.current_testsuite_data.tests.append(self.current_test_data)
        self.for_each_reporting_sessions(lambda b: b.begin_test(test))
        self.current_step_data_list = self.current_test_data.steps
            
    def end_test(self):
        if self.current_test_data.outcome == None:
            self.current_test_data.outcome = True
        self.current_test_data.end_time = time.time()
        
        self.for_each_reporting_sessions(lambda b: b.end_test(self.current_test, self.current_test_data.outcome))

        self.current_test = None
        self.current_test_data = None

    def create_step_if_needed(self):
        if not self.current_step_data_list:
            self.set_step(self.default_step_description)

    def set_step(self, description, force_lock=False):
        if self.step_lock and not force_lock:
            return

        self.current_step = description
        self.current_step_data = StepData(description)

        # remove previous step from report data if it was empty
        if self.current_step_data_list and not self.current_step_data_list[-1].entries:
            del self.current_step_data_list[-1]
        self.current_step_data_list.append(self.current_step_data)

        self.for_each_reporting_sessions(lambda b: b.set_step(description))
        
    def log(self, level, content):
        self.create_step_if_needed()
        self.current_step_data.entries.append(LogData(level, content))
        self.for_each_reporting_sessions(lambda b: b.log(level, content))
    
    def log_debug(self, content):
        self.log(LOG_LEVEL_DEBUG, content)
    
    def log_info(self, content):
        self.log(LOG_LEVEL_INFO, content)
    
    def log_warn(self, content):
        self.log(LOG_LEVEL_WARN, content)
    
    def log_error(self, content):
        if self.current_test_data:
            self.current_test_data.outcome = False
        self.log(LOG_LEVEL_ERROR, content)
    
    def check(self, description, outcome, details=None):
        if not self.current_test:
            raise LemonCheesecakeInternalError("A check can only be associated to a test not a test suite")
        
        self.create_step_if_needed()
        self.current_step_data.entries.append(CheckData(description, outcome, details))
        
        if outcome == False:
            self.current_test_data.outcome = False
        
        self.for_each_reporting_sessions(lambda b: b.check(description, outcome, details))
        
        return outcome
    
    def prepare_attachment(self, filename, description=None):
        self.create_step_if_needed()
        
        if not description:
            description = filename
        
        attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
        self.attachment_count += 1
        if not os.path.exists(self.attachments_dir):
            os.mkdir(self.attachments_dir)
        self.current_step_data.entries.append(AttachmentData(description, "%s/%s" % (ATTACHEMENT_DIR, attachment_filename)))
        
        return os.path.join(self.attachments_dir, attachment_filename)
        # TODO: add hook for attachment
    
    def save_attachment_file(self, filename, description=None):
        target_filename = self.prepare_attachment(os.path.basename(filename), description)
        shutil.copy(filename, target_filename)
    
    def save_attachment_content(self, content, filename, description=None):
        target_filename = self.prepare_attachment(filename, description)
        
        fh = open(target_filename, "w")
        fh.write(content)
        fh.close()
    
def log_debug(content):
    """
    Log a debug level message.
    """
    get_runtime().log_debug(content)

def log_info(content):
    """
    Log a info level message.
    """
    get_runtime().log_info(content)

def log_warning(content):
    """
    Log a warning level message.
    """
    get_runtime().log_warn(content)

log_warn = log_warning

def log_error(content):
    """
    Log an error level message.
    """
    get_runtime().log_error(content)

def set_step(description):
    """
    Set a new step.
    """
    get_runtime().set_step(description)

def prepare_attachment(filename, description=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return get_runtime().prepare_attachment(filename, description)

def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    get_runtime().save_attachment_file(filename, description)

def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description)
