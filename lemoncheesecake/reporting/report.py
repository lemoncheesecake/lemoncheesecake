'''
Created on Mar 26, 2016

@author: nicolas
'''

import time
import re
from decimal import Decimal

from lemoncheesecake.consts import LOG_LEVEL_ERROR, LOG_LEVEL_WARN
from lemoncheesecake.utils import humanize_duration

__all__ = (
    "LogData", "CheckData", "AttachmentData", "UrlData", "StepData", "TestData",
    "TestSuiteData", "HookData", "Report"
)

TEST_STATUSES = "passed", "failed", "skipped"

# NB: it would be nicer to use:
# datetime.isoformat(sep=' ', timespec='milliseconds')
# unfortunately, the timespec argument is only available since Python 3.6

def format_timestamp(ts):
    ts = round(ts, 3)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) + (".%03d" % (Decimal(repr(ts)) % 1 * 1000))

def parse_timestamp(s):
    m = re.compile("(.+)\.(\d+)").match(s)
    if not m:
        raise ValueError("s is not valid datetime representation with milliseconds precision")
    
    dt, milliseconds = m.group(1), int(m.group(2))
    
    return time.mktime(time.strptime(dt, "%Y-%m-%d %H:%M:%S")) + float(milliseconds) / 1000

class LogData:
    def __init__(self, level, message, ts):
        self.level = level
        self.message = message
        self.time = ts
    
    def has_failure(self):
        return self.level == LOG_LEVEL_ERROR

class CheckData:
    def __init__(self, description, outcome, details=None):
        self.description = description
        self.outcome = outcome
        self.details = details
    
    def has_failure(self):
        return self.outcome == False

class AttachmentData:
    def __init__(self, description, filename):
        self.description = description
        self.filename = filename
    
    def has_failure(self):
        return False

class UrlData:
    def __init__(self, description, url):
        self.description = description
        self.url = url
    
    def has_failure(self):
        return False

class StepData:
    def __init__(self, description):
        self.description = description
        self.entries = [ ]
        self.start_time = None
        self.end_time = None
    
    def has_failure(self):
        return len(list(filter(lambda entry: entry.has_failure(), self.entries))) > 0
        
class TestData:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.status = None
        self.status_details = None
        self.steps = [ ]
        self.start_time = None
        self.end_time = None
    
    def has_failure(self):
        return len(list(filter(lambda step: step.has_failure(), self.steps))) > 0

class HookData:
    def __init__(self):
        self.steps = [ ]
        self.start_time = None
        self.end_time = None
        self.outcome = None
    
    def has_failure(self):
        return len(list(filter(lambda step: step.has_failure(), self.steps))) > 0
    
    def is_empty(self):
        return len(self.steps) == 0

class TestSuiteData:
    def __init__(self, name, description, parent=None):
        self.name = name
        self.description = description
        self.parent = parent
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.suite_setup = None
        self.tests = [ ]
        self.sub_testsuites = [ ]
        self.suite_teardown = None
    
    def get_test(self, test_name):
        for test in self.tests:
            if test.name == test_name:
                return test
        
        for suite in self.sub_testsuites:
            test = suite.get_test(test_name)
            if test:
                return test
        
        return None
    
    def get_suite(self, suite_name):
        if self.name == suite_name:
            return self
        
        for sub_suite in self.sub_testsuites:
            suite = sub_suite.get_suite(suite_name)
            if suite:
                return suite
        
        return None

class ReportStats:
    def __init__(self, report):
        self.tests = 0
        self.test_statuses = {s: 0 for s in TEST_STATUSES}
        self.errors = 0
        self.checks = 0
        self.check_successes = 0
        self.check_failures = 0
        self.error_logs = 0
        self.warning_logs = 0
        
        if report.test_session_setup:
            if report.test_session_setup.has_failure():
                self.errors += 1
            self._walk_steps(report.test_session_setup.steps)
        
        if report.test_session_teardown:
            if report.test_session_teardown.has_failure():
                self.errors += 1
            self._walk_steps(report.test_session_teardown.steps)
        
        for suite in report.testsuites:
            self._walk_testsuite(suite)
    
    def _walk_steps(self, steps):
        for step in steps:
            for entry in step.entries:
                if isinstance(entry, CheckData):
                    self.checks += 1
                    if entry.outcome == True:
                        self.check_successes += 1
                    elif entry.outcome == False:
                        self.check_failures += 1
                if isinstance(entry, LogData):
                    if entry.level == LOG_LEVEL_WARN:
                        self.warning_logs += 1
                    elif entry.level == LOG_LEVEL_ERROR:
                        self.error_logs += 1
        
    def _walk_testsuite(self, suite):
        if suite.suite_setup:
            if suite.suite_setup.has_failure():
                self.errors += 1
            self._walk_steps(suite.suite_setup.steps)
        
        if suite.suite_teardown:
            if suite.suite_teardown.has_failure():
                self.errors += 1
            self._walk_steps(suite.suite_teardown.steps)
        
        for test in suite.tests:
            self.tests += 1
            if test.status != None:
                self.test_statuses[test.status] += 1
            self._walk_steps(test.steps)
        
        for sub_suite in suite.sub_testsuites:
            self._walk_testsuite(sub_suite)

class Report:
    def __init__(self):
        self.info = [ ]
        self.test_session_setup = None
        self.test_session_teardown = None
        self.testsuites = [ ]
        self.start_time = None
        self.end_time = None
        self.report_generation_time = None
    
    def add_info(self, name, value):
        self.info.append([name, value])

    def get_test(self, test_name):
        for suite in self.testsuites:
            test = suite.get_test(test_name)
            if test:
                return test
        
        return None
    
    def get_suite(self, suite_name):
        for suite in self.testsuites:
            if suite.name == suite_name:
                return suite
            sub_suite = suite.get_suite(suite_name)
            if sub_suite:
                return sub_suite
        
        return None
    
    def get_stats(self):
        return ReportStats(self)
    
    def serialize_stats(self):
        stats = self.get_stats()
        return (
            ("Start time", time.asctime(time.localtime(self.start_time))),
            ("End time", time.asctime(time.localtime(self.end_time)) if self.end_time else "n/a"),
            ("Duration", humanize_duration(self.end_time - self.start_time) if self.end_time else "n/a"),
            ("Tests", str(stats.tests)),
            ("Successful tests", str(stats.test_statuses["passed"])),
            ("Successful tests in %", "%d%%" % (float(stats.test_statuses["passed"]) / stats.tests * 100 if stats.tests else 0)),
            ("Failed tests", str(stats.test_statuses["failed"])),
            ("Skipped tests", str(stats.test_statuses["skipped"])),
            ("Errors", str(stats.errors))
        )
