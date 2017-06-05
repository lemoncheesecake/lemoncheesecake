'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import os.path
import time
import shutil

from lemoncheesecake.utils import humanize_duration
from lemoncheesecake.exceptions import LemonCheesecakeInternalError
from lemoncheesecake.consts import ATTACHEMENT_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import *

__all__ = "log_debug", "log_info", "log_warn", "log_warning", "log_error", "log_url", "set_step", \
    "prepare_attachment", "save_attachment_file", "save_attachment_content", \
    "add_report_info"

_runtime = None # singleton

def initialize_runtime(reporting_backends, report_dir):
    global _runtime
    _runtime = _Runtime(reporting_backends, report_dir)

def get_runtime():
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime

class _Runtime:
    def __init__(self, reporting_backends, report_dir):
        self.reporting_backends = reporting_backends
        self.report_dir = report_dir
        self.attachments_dir = os.path.join(self.report_dir, ATTACHEMENT_DIR)
        self.attachment_count = 0
        self.report = Report()
        self.reporting_sessions = []
        self.step_lock = False
        self.default_step_description = None
        # pointers to report data parts
        self.current_testsuite_data = None
        self.current_test_data = None
        self.current_step_data_list = None
        self.current_step_data = None
        # pointers to running test/testsuite
        self.current_test = None
        self.current_testsuite = None
        # for test / testsuite hook / before/after all tests outcome
        self.has_pending_failure = False
    
    def initialize_reporting_sessions(self):
        for backend in self.reporting_backends:
            session = backend.create_reporting_session(self.report_dir, self.report)
            self.reporting_sessions.append(session)
            
    def for_each_reporting_sessions(self, callback):
        for session in self.reporting_sessions:
            callback(session)
    
    def _start_hook(self, ts):
        self.has_pending_failure = False
        hook_data = HookData()
        hook_data.start_time = ts
        return hook_data
    
    def _end_hook(self, hook_data, ts):
        if hook_data:
            hook_data.end_time = ts
            hook_data.outcome = not self.has_pending_failure

    def end_current_step(self, ts):
        if self.current_step_data:
            self.current_step_data.end_time = ts
            self.current_step_data = None

        # remove previous step from report data if it was empty
        if self.current_step_data_list and len(self.current_step_data_list[-1].entries) == 0:
            del self.current_step_data_list[-1]
        
    def begin_tests(self):
        self.report.start_time = time.time()
        self.for_each_reporting_sessions(lambda b: b.begin_tests())
    
    def end_tests(self):
        self.report.end_time = time.time()
        self.report.report_generation_time = self.report.end_time
        self.for_each_reporting_sessions(lambda b: b.end_tests())
    
    def begin_test_session_setup(self):
        self.report.test_session_setup = self._start_hook(time.time())
        self.current_step_data_list = self.report.test_session_setup.steps
        self.default_step_description = "Setup test session"
    
        self.for_each_reporting_sessions(lambda b: b.begin_test_session_setup())
    
    def end_test_session_setup(self):
        if self.report.test_session_setup.is_empty():
            self.report.test_session_setup = None
        else: 
            now = time.time()
            self._end_hook(self.report.test_session_setup, now)
            self.end_current_step(now)
        self.for_each_reporting_sessions(lambda b: b.end_test_session_setup())

    def begin_test_session_teardown(self):
        self.report.test_session_teardown = self._start_hook(time.time())
        self.current_step_data_list = self.report.test_session_teardown.steps
        self.default_step_description = "Teardown test session"
        
        self.for_each_reporting_sessions(lambda b: b.begin_test_session_teardown())
    
    def end_test_session_teardown(self):
        if self.report.test_session_teardown.is_empty():
            self.report.test_session_teardown = None
        else:
            now = time.time()
            self._end_hook(self.report.test_session_teardown, now)
            self.end_current_step(now)
        self.for_each_reporting_sessions(lambda b: b.end_test_session_teardown())

    def begin_suite(self, testsuite):
        self.current_testsuite = testsuite
        suite_data = TestSuiteData(testsuite.name, testsuite.description, self.current_testsuite_data)
        suite_data.tags.extend(testsuite.tags)
        suite_data.properties.update(testsuite.properties)
        suite_data.links.extend(testsuite.links)
        if self.current_testsuite_data:
            self.current_testsuite_data.sub_testsuites.append(suite_data)
        else:
            self.report.testsuites.append(suite_data)
        self.current_testsuite_data = suite_data
        
        self.for_each_reporting_sessions(lambda b: b.begin_suite(testsuite))
    
    def begin_suite_setup(self):
        self.current_testsuite_data.suite_setup = self._start_hook(time.time())
        self.current_step_data_list = self.current_testsuite_data.suite_setup.steps
        self.default_step_description = "Setup suite"

        self.for_each_reporting_sessions(lambda b: b.begin_suite_setup(self.current_testsuite))
    
    def end_suite_setup(self):
        if self.current_testsuite_data.suite_setup.is_empty():
            self.current_testsuite_data.suite_setup = None
        else:
            now = time.time()
            self._end_hook(self.current_testsuite_data.suite_setup, now)
            self.end_current_step(now)
        self.for_each_reporting_sessions(lambda b: b.end_suite_setup(self.current_testsuite))
        
    def begin_suite_teardown(self):
        self.current_testsuite_data.suite_teardown = self._start_hook(time.time())
        self.current_step_data_list = self.current_testsuite_data.suite_teardown.steps
        self.default_step_description = "Teardown suite"
            
        self.for_each_reporting_sessions(lambda b: b.begin_suite_teardown(self.current_testsuite))

    def end_suite_teardown(self):
        if self.current_testsuite_data.suite_teardown.is_empty():
            self.current_testsuite_data.suite_teardown = None
        else:
            now = time.time()
            self.end_current_step(now)
            self._end_hook(self.current_testsuite_data.suite_teardown, now)
        self.for_each_reporting_sessions(lambda b: b.end_suite_teardown(self.current_testsuite))
    
    def end_suite(self):
        self.for_each_reporting_sessions(lambda b: b.end_suite(self.current_testsuite))
        self.current_testsuite_data = self.current_testsuite_data.parent
        self.current_testsuite = self.current_testsuite.parent_suite
        
    def begin_test(self, test):
        now = time.time()
        self.has_pending_failure = False
        self.current_test = test
        self.current_test_data = TestData(test.name, test.description)
        self.current_test_data.tags.extend(test.tags)
        self.current_test_data.properties.update(test.properties)
        self.current_test_data.links.extend(test.links)
        self.current_test_data.start_time = now
        self.current_testsuite_data.tests.append(self.current_test_data)
        self.for_each_reporting_sessions(lambda b: b.begin_test(test))
        self.current_step_data_list = self.current_test_data.steps
        self.default_step_description = test.description
    
    def begin_test_setup(self):
        self.set_step("Setup test")
    
    def end_test_setup(self):
        self.set_step(self.current_test.description)
    
    def begin_test_teardown(self):
        self.set_step("Teardown test")
    
    def end_test_teardown(self):
        pass
    
    def end_test(self):
        now = time.time()
        self.current_test_data.status = "failed" if self.has_pending_failure else "passed"
        self.current_test_data.end_time = now
        self.end_current_step(now)
        
        self.for_each_reporting_sessions(lambda b: b.end_test(self.current_test, self.current_test_data.status))

        self.current_test = None
        self.current_test_data = None
        self.current_step_data_list = None
    
    def _bypass_test(self, test, status, status_details):
        now = time.time()
        
        test_data = TestData(test.name, test.description)
        test_data.tags.extend(test.tags)
        test_data.properties.update(test.properties)
        test_data.links.extend(test.links)
        test_data.end_time = test_data.start_time = now
        test_data.status = status
        test_data.status_details = status_details
        self.current_testsuite_data.tests.append(test_data)

        self.for_each_reporting_sessions(lambda b: b.bypass_test(test, status, status_details))
    
    def skip_test(self, test, reason):
        self._bypass_test(test, "skipped", reason)
    
    def create_step_if_needed(self, ts=None):
        if not self.current_step_data_list:
            self._set_step(self.default_step_description, ts or time.time())

    def _set_step(self, description, ts):
        self.end_current_step(ts)
        
        self.current_step_data = StepData(description)
        self.current_step_data.start_time = ts

        self.current_step_data_list.append(self.current_step_data)

        self.for_each_reporting_sessions(lambda b: b.set_step(description))
        
    def set_step(self, description, force_lock=False):
        if self.step_lock and not force_lock:
            return
        
        self._set_step(description, time.time())
        
    def log(self, level, content):
        now = time.time()
        self.create_step_if_needed(now)
        self.current_step_data.entries.append(LogData(level, content, now))
        self.for_each_reporting_sessions(lambda b: b.log(level, content))
    
    def log_debug(self, content):
        self.log(LOG_LEVEL_DEBUG, content)
    
    def log_info(self, content):
        self.log(LOG_LEVEL_INFO, content)
    
    def log_warn(self, content):
        self.log(LOG_LEVEL_WARN, content)
    
    def log_error(self, content):
        self.has_pending_failure = True
        self.log(LOG_LEVEL_ERROR, content)
    
    def check(self, description, outcome, details=None):
        self.create_step_if_needed()
        self.current_step_data.entries.append(CheckData(description, outcome, details))
        
        if outcome == False:
            self.has_pending_failure = True
        
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
    
    def save_attachment_content(self, content, filename, description=None, binary_mode=False):
        target_filename = self.prepare_attachment(filename, description)
        
        fh = open(target_filename, "wb")
        fh.write(content if binary_mode else content.encode("utf-8"))
        fh.close()
    
    def log_url(self, url, description=None):
        self.create_step_if_needed()
        
        if not description:
            description = url
        
        self.current_step_data.entries.append(UrlData(description, url))        
        # TODO: add hook for URL

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

def save_attachment_content(content, filename, description=None, binary_mode=False):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description, binary_mode)

def log_url(url, description=None):
    """
    Log an URL.
    """
    get_runtime().log_url(url, description)

def add_report_info(name, value):
    report = get_runtime().report
    report.add_info(name, value)
