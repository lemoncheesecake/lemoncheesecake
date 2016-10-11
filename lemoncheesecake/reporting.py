'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import LemonCheesecakeException, UnknownReportBackendError

ATTACHEMENT_DIR = "attachments"

LOG_LEVEL_DEBUG = "debug"
LOG_LEVEL_INFO = "info"
LOG_LEVEL_WARN = "warn"
LOG_LEVEL_ERROR = "error"

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
    
    def log(self, level, content):
        pass
    
    def check(self, description, outcome, details=None):
        pass

def register_default_backends():
    from lemoncheesecake.reportingbackends.console import ConsoleBackend
    from lemoncheesecake.reportingbackends.xml import XmlBackend
    from lemoncheesecake.reportingbackends.json_ import JsonBackend
    from lemoncheesecake.reportingbackends.html import HtmlBackend

    backends = ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend
    for backend in backends:
        register_backend(backend.name, backend())
    
    only_enable_backends((ConsoleBackend.name, JsonBackend.name, HtmlBackend.name))

register_default_backends()