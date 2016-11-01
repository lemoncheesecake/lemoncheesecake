'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import UnknownReportBackendError

__all__ = (
    "register_backend", "get_backend", "has_backend", "enable_backend", "disable_backend", 
    "only_enable_backends", "get_enabled_backend_names", "get_enabled_backends",
    "register_default_backends",
    "ReportingBackend"
)

_backends = { }
_enabled_backends = set()

def _assert_backend_name(name):
    if name not in _backends:
        raise UnknownReportBackendError(name)

def register_backend(name, backend):
    global _backends
    _backends[name] = backend

def get_backend(name):
    global _backends
    _assert_backend_name(name)
    return _backends[name]

def has_backend(name):
    global _backends
    return name in _backends

def enable_backend(name):
    _assert_backend_name(name)
    _enabled_backends.add(name)

def disable_backend(name):
    _assert_backend_name(name)
    _enabled_backends.discard(name)

def only_enable_backends(names):
    for name in names:
        _assert_backend_name(name)

    _enabled_backends.clear()
    _enabled_backends.update(names)

def get_enabled_backend_names():
    return list(_enabled_backends)

def get_enabled_backends():
    return [_backends[b] for b in _enabled_backends]

class ReportingBackend:
    def initialize(self, report, report_dir):
        self.report = report
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
    
    def log(self, level, content):
        pass
    
    def check(self, description, outcome, details=None):
        pass

def register_default_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend

    backends = ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend
    for backend in backends:
        register_backend(backend.name, backend())
    
    only_enable_backends((ConsoleBackend.name, JsonBackend.name, HtmlBackend.name))

register_default_backends()
