'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.common import LemonCheesecakeException

_backends = { }

def register_backend(name, backend):
    global _backends
    _backends[name] = backend

def get_backend(name):
    global _backends
    if not _backends.has_key(name):
        raise LemonCheesecakeException("Unknown reporting backend: '%s'" % name)
    return _backends[name]

def has_backend(name):
    global _backends
    return _backends.has_key(name)

class ReportingBackend:
    def initialize(self, test_results, report_dir):
        self.test_results = test_results
        self.report_dir = report_dir
    
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