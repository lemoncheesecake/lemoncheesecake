'''
Created on Mar 26, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import LOG_LEVEL_ERROR, LOG_LEVEL_WARN

class LogData:
    def __init__(self, level, message):
        self.level = level
        self.message = message

class CheckData:
    def __init__(self, description, outcome, details=None):
        self.description = description
        self.outcome = outcome
        self.details = details

class StepData:
    def __init__(self, description):
        self.description = description
        self.entries = [ ]
        
class TestData:
    def __init__(self, id, description):
        self.id = id
        self.description = description
        self.outcome = None
        self.steps = [ ]

class TestSuiteData:
    def __init__(self, id, description, parent=None):
        self.id = id
        self.description = description
        self.parent = parent
        self.tests = [ ]
        self.sub_testsuites = [ ]

class ReportingData:
    def __init__(self):
        self.testsuites = [ ]
        self.reset_stats()
    
    def reset_stats(self):
        self.tests = 0
        self.tests_success = 0
        self.tests_failure = 0
        self.checks = 0
        self.checks_success = 0
        self.checks_failure = 0
        self.errors = 0
        self.warnings = 0
    
    def _walk_testsuite(self, suite):
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
                            self.check_success += 1
                        elif entry.outcome == False:
                            self.check_failure += 1
                    if type(entry) == LogData:
                        if entry.type == LOG_LEVEL_WARN:
                            self.warnings += 1
                        elif entry.type == LOG_LEVEL_ERROR:
                            self.errors += 1
        
        for sub_suite in suite.sub_testsuites:
            self._walk_testsuite(sub_suite)
    
    def refresh_stats(self):
        self.reset_stats()
        for suite in self.testsuites:
            self._walk_testsuite(suite)