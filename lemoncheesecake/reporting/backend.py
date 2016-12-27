'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import UnknownReportBackendError, MethodNotImplemented
from lemoncheesecake.utils import object_has_method

__all__ = (
    "register_backend", "get_backend", "has_backend", "enable_backend", "disable_backend", 
    "set_enabled_backends", "get_backend_names", "get_backends",
    "register_default_backends",
    "ReportingBackend", "ReportingSession"
)

_backends = { }
_enabled_backends = set()

CAPABILITY_REPORTING_SESSION = 0x1
CAPABILITY_SERIALIZE = 0x2
CAPABILITY_UNSERIALIZE = 0x4

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

def set_enabled_backends(names):
    for name in names:
        _assert_backend_name(name)

    _enabled_backends.clear()
    _enabled_backends.update(names)

def get_backends(capabilities=CAPABILITY_REPORTING_SESSION, enabled_backends_only=True):
    backend_names = _enabled_backends if enabled_backends_only else _backends.keys()
    return [
        _backends[name] for name in backend_names if _backends[name].get_capabilities() & capabilities == capabilities
    ]

def get_backend_names(capabilities=CAPABILITY_REPORTING_SESSION, enabled_backends_only=True):
    return [ backend.name for backend in get_backends(capabilities, enabled_backends_only) ]

class ReportingSession:
    def __init__(self, report, report_dir):
        self.report = report
        self.report_dir = report_dir
    
    def begin_tests(self):
        pass
    
    def end_tests(self):
        pass
    
    def begin_worker_before_all_tests(self):
        pass
    
    def end_worker_after_all_tests(self):
        pass
    
    def begin_suite(self, testsuite):
        pass
    
    def begin_before_suite(self, testsuite):
        pass
    
    def end_before_suite(self, testsuite):
        pass
        
    def begin_after_suite(self, testsuite):
        pass
    
    def end_after_suite(self, testsuite):
        pass
    
    def end_suite(self, testsuite):
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
    def is_available(self):
        return True
    
    def get_capabilities(self):
        capabilities = 0
        if object_has_method(self, "create_reporting_session"):
            capabilities |= CAPABILITY_REPORTING_SESSION
        if object_has_method(self, "serialize_report"):
            capabilities |= CAPABILITY_SERIALIZE
        if object_has_method(self, "unserialize_report"):
            capabilities |= CAPABILITY_UNSERIALIZE
        return capabilities
    
#     def create_reporting_session(self, report, report_dir):
#         pass
#     
#     def serialize_report(self, report, report_dir):
#         pass
#     
#     def unserialize_report(self, report_path):
#         pass

class FileReportSession(ReportingSession):
    def __init__(self, report, report_dir, backend):
        ReportingSession.__init__(self, report, report_dir)
        self.backend = backend
    
    def end_tests(self):
        self.backend.serialize_report(self.report, self.report_dir)

class FileReportBackend(ReportingBackend):
    def serialize_report(self, report, report_dir):
        raise MethodNotImplemented(self, "serialize_report")
    
    def create_reporting_session(self, report, report_dir):
        return FileReportSession(report, report_dir, self)

def register_default_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend

    backends = ConsoleBackend(), XmlBackend(), JsonBackend(), HtmlBackend()
    enabled_backends = []
    for backend in backends:
        if backend.is_available():
            register_backend(backend.name, backend)
            if backend.name != "xml":
                enabled_backends.append(backend) 
    
    set_enabled_backends([backend.name for backend in enabled_backends])

register_default_backends()
