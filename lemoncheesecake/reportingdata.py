'''
Created on Mar 26, 2016

@author: nicolas
'''

from lemoncheesecake.reporting import LOG_LEVEL_ERROR, LOG_LEVEL_WARN

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

class TestSuiteData:
    def __init__(self, id, description, parent=None):
        self.id = id
        self.description = description
        self.parent = parent
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.before_suite_steps = [ ]
        self.before_suite_start_time = None
        self.before_suite_end_time = None
        self.tests = [ ]
        self.sub_testsuites = [ ]
        self.after_suite_steps = [ ]
        self.after_suite_start_time = None
        self.after_suite_end_time = None
    
    def before_suite_has_failure(self):
        return len(filter(lambda step: step.has_failure(), self.before_suite_steps)) > 0

    def after_suite_has_failure(self):
        return len(filter(lambda step: step.has_failure(), self.after_suite_steps)) > 0

class ReportingData:
    def __init__(self):
        self.info = [ ]
        self.stats = [ ]
        self.testsuites = [ ]
        self.start_time = None
        self.end_time = None
        self.report_generation_time = None
        self.reset_stats()
    
    def add_info(self, name, value):
        self.info.append([name, value])
    
    def add_stats(self, name, value):
        self.stats.append([name, value])
    
    def reset_stats(self):
        self.tests = 0
        self.tests_success = 0
        self.tests_failure = 0
        self.errors = 0
        self.checks = 0
        self.checks_success = 0
        self.checks_failure = 0
        self.error_logs = 0
        self.warning_logs = 0
    
    def _walk_testsuite(self, suite):
        if suite.before_suite_has_failure():
            self.errors += 1
        
        if suite.after_suite_has_failure():
            self.errors += 1
        
        for test in suite.tests:
            self.tests += 1
            if test.outcome == True:
                self.tests_success += 1
            elif test.outcome == False:
                self.tests_failure += 1
            for step in test.steps:
                for entry in step.entries:
                    if type(entry) == CheckData:
                        self.checks += 1
                        if entry.outcome == True:
                            self.checks_success += 1
                        elif entry.outcome == False:
                            self.checks_failure += 1
                    if type(entry) == LogData:
                        if entry.level == LOG_LEVEL_WARN:
                            self.warning_logs += 1
                        elif entry.level == LOG_LEVEL_ERROR:
                            self.error_logs += 1
        
        for sub_suite in suite.sub_testsuites:
            self._walk_testsuite(sub_suite)
    
    def refresh_stats(self):
        self.reset_stats()
        for suite in self.testsuites:
            self._walk_testsuite(suite)
