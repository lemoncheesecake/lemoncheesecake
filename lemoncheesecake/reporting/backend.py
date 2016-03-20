'''
Created on Mar 19, 2016

@author: nicolas
'''

class Backend:
    def __init__(self, runtime_state):
        self.runtime_state = runtime_state
    
    def begin_tests(self):
        pass
    
    def end_tests(self):
        pass
    
    def begin_testsuite(self, testsuite):
        pass
    
    def end_testsuite(self):
        pass
    
    def begin_test(self, test):
        pass
    
    def end_test(self):
        pass
    
    def set_step(self, description):
        pass
    
    def log(self, content, level):
        pass