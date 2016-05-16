'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.common import LemonCheesecakeException

class ReportingBackend:
    def initialize(self, reporting_data, report_dir):
        self.reporting_data = reporting_data
        self.report_dir = report_dir
    
    def begin_tests(self):
        pass
    
    def end_tests(self):
        pass
    
    def begin_before_suite(self, testsuite):
        pass
    
    def end_before_suite(self, testsuite):
        pass
    
    def begin_after_suite(self, testsuite):
        pass
    
    def end_after_suite(self, testsuite):
        pass
    
    def begin_test(self, test):
        pass
    
    def end_test(self, test, outcome):
        pass
    
    def set_step(self, description):
        pass
    
    def log(self, content, level):
        pass
    
    def check(self, description, outcome, details=None):
        pass