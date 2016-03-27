'''
Created on Mar 19, 2016

@author: nicolas
'''

class Backend:
    def initialize(self, test_results):
        self.test_results = test_results
    
    def begin_tests(self):
        pass
    
    def end_tests(self):
        pass
    
    def begin_testsuite(self, testsuite):
        pass
    
    def end_testsuite(self, testsuite):
        pass
    
    def begin_test(self, test):
        pass
    
    def end_test(self, test, outcome):
        pass
    
    def set_step(self, description):
        pass
    
    def log(self, content, level):
        pass