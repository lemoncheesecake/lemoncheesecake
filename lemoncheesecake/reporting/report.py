'''
Created on Mar 26, 2016

@author: nicolas
'''

import time

from lemoncheesecake.consts import LOG_LEVEL_ERROR, LOG_LEVEL_WARN
from lemoncheesecake.utils import humanize_duration

__all__ = (
    "LogData", "CheckData", "AttachmentData", "StepData", "TestData",
    "TestSuiteData", "HookData", "Report"
)

class LogData:
    def __init__(self, level, message):
        self.level = level
        self.message = message
    
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

class StepData:
    def __init__(self, description):
        self.description = description
        self.entries = [ ]
    
    def has_failure(self):
        return len(filter(lambda entry: entry.has_failure(), self.entries)) > 0
        
class TestData:
    def __init__(self, id, description):
        self.id = id
        self.description = description
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.outcome = None
        self.steps = [ ]
        self.start_time = None
        self.end_time = None
    
    def has_failure(self):
        return len(filter(lambda step: step.has_failure(), self.steps)) > 0

class HookData:
    def __init__(self):
        self.steps = [ ]
        self.start_time = None
        self.end_time = None
    
    def has_failure(self):
        return len(filter(lambda step: step.has_failure(), self.steps)) > 0

class TestSuiteData:
    def __init__(self, id, description, parent=None):
        self.id = id
        self.description = description
        self.parent = parent
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.before_suite = None
        self.tests = [ ]
        self.sub_testsuites = [ ]
        self.after_suite = None
    
    def get_test(self, test_id):
        for test in self.tests:
            if test.id == test_id:
                return test
        
        for suite in self.sub_testsuites:
            test = suite.get_test(test_id)
            if test:
                return test
        
        return None
    
    def get_suite(self, suite_id):
        if self.id == suite_id:
            return self
        
        for sub_suite in self.sub_testsuites:
            suite = sub_suite.get_suite(suite_id)
            if suite:
                return suite
        
        return None

class ReportStats:
    def __init__(self, report):
        self.tests = 0
        self.test_successes = 0
        self.test_failures = 0
        self.errors = 0
        self.checks = 0
        self.check_successes = 0
        self.check_failures = 0
        self.error_logs = 0
        self.warning_logs = 0
        
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
        if suite.before_suite:
            if suite.before_suite.has_failure():
                self.errors += 1
            self._walk_steps(suite.before_suite.steps)
        
        if suite.after_suite:
            if suite.after_suite.has_failure():
                self.errors += 1
            self._walk_steps(suite.after_suite.steps)
        
        for test in suite.tests:
            self.tests += 1
            if test.outcome == True:
                self.test_successes += 1
            elif test.outcome == False:
                self.test_failures += 1
            self._walk_steps(test.steps)
        
        for sub_suite in suite.sub_testsuites:
            self._walk_testsuite(sub_suite)

class Report:
    def __init__(self):
        self.info = [ ]
        self.testsuites = [ ]
        self.start_time = None
        self.end_time = None
        self.report_generation_time = None
    
    def add_info(self, name, value):
        self.info.append([name, value])

    def get_test(self, test_id):
        for suite in self.testsuites:
            test = suite.get_test(test_id)
            if test:
                return test
        
        return None
    
    def get_suite(self, suite_id):
        for suite in self.testsuites:
            if suite.id == suite_id:
                return suite
            sub_suite = suite.get_suite(suite_id)
            if sub_suite:
                return sub_suite
        
        return None
    
    def get_stats(self):
        return ReportStats(self)
    
    def serialize_stats(self):
        stats = self.get_stats()
        return (
            ("Start time", time.asctime(time.localtime(self.start_time))),
            ("End time", time.asctime(time.localtime(self.end_time))),
            ("Duration", humanize_duration(self.end_time - self.start_time)),
            ("Tests", str(stats.tests)),
            ("Successful tests", str(stats.test_successes)),
            ("Successful tests in %", "%d%%" % (float(stats.test_successes) / stats.tests * 100 if stats.tests else 0)),
            ("Failed tests", str(stats.test_failures)),
            ("Errors", str(stats.errors))
        )
