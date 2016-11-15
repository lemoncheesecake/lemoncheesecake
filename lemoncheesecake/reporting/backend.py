'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import UnknownReportBackendError, MethodNotImplemented

__all__ = (
    "register_backend", "get_backend", "has_backend", "enable_backend", "disable_backend", 
    "only_enable_backends", "get_enabled_backend_names", "get_enabled_backends",
    "register_default_backends",
    "ReportingBackend", "ReportingSession"
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

class ReportingSession:
    def __init__(self, report, report_dir):
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

class ReportingBackend:
    def can_handle_reporting_session(self):
        return False
    
    def can_serialize_report(self):
        return False
    
    def can_unserialize_report(self):
        return False
    
    def create_reporting_session(self, report, report_dir):
        raise MethodNotImplemented(self, "create_reporting_session")
    
    def serialize_report(self, report, report_dir):
        raise MethodNotImplemented(self, "serialize_report")
    
    def unserialize_report_from_file(self, report_filename):
        raise MethodNotImplemented(self, "unserialize_report_from_file")
    
    def unserialize_report_from_dir(self, report_dir):
        raise MethodNotImplemented(self, "unserialize_report_from_dir")

class FileReportSession(ReportingSession):
    def __init__(self, report, report_dir, backend):
        ReportingSession.__init__(self, report, report_dir)
        self.backend = backend
    
    def end_tests(self):
        self.backend.serialize_report(self.report, self.report_dir)

class FileReportBackend(ReportingBackend):
    def can_handle_reporting_session(self):
        return True
    
    def can_serialize_report(self):
        return True
    
    def create_reporting_session(self, report, report_dir):
        return FileReportSession(report, report_dir, self)

def register_default_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend

    backends = ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend
    for backend in backends:
        register_backend(backend.name, backend())
    
    only_enable_backends((ConsoleBackend.name, JsonBackend.name, HtmlBackend.name))

register_default_backends()
