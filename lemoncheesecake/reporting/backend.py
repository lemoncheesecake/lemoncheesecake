'''
Created on Mar 29, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import MethodNotImplemented
from lemoncheesecake.utils import object_has_method

__all__ = (
    "get_available_backends", "ReportingBackend", "ReportingSession",
    "CAPABILITY_REPORTING_SESSION", "CAPABILITY_SERIALIZE", "CAPABILITY_UNSERIALIZE"
)

CAPABILITY_REPORTING_SESSION = 0x1
CAPABILITY_SERIALIZE = 0x2
CAPABILITY_UNSERIALIZE = 0x4

SAVE_AT_END_OF_TESTS = 1
SAVE_AT_EACH_TESTSUITE = 2
SAVE_AT_EACH_TEST = 3
SAVE_AT_EACH_FAILED_TEST = 4
SAVE_AT_EACH_EVENT = 5

class ReportingSession:
    def __init__(self, report, report_dir):
        self.report = report
        self.report_dir = report_dir
    
    def begin_tests(self):
        pass
    
    def end_tests(self):
        pass
    
    def begin_test_session_setup(self):
        pass
    
    def end_test_session_setup(self):
        pass
    
    def begin_test_session_teardown(self):
        pass
    
    def end_test_session_teardown(self):
        pass
    
    def begin_suite(self, testsuite):
        pass
    
    def begin_suite_setup(self, testsuite):
        pass
    
    def end_suite_setup(self, testsuite):
        pass
        
    def begin_suite_teardown(self, testsuite):
        pass
    
    def end_suite_teardown(self, testsuite):
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
    def __init__(self, report, report_dir, backend, save_mode):
        ReportingSession.__init__(self, report, report_dir)
        self.backend = backend
        self.save_mode = save_mode
    
    def save(self):
        self.backend.serialize_report(self.report, self.report_dir)
    
    def _handle_code_end(self, is_failure):
        if (self.save_mode == SAVE_AT_EACH_TEST) or (self.save_mode == SAVE_AT_EACH_FAILED_TEST and is_failure):
            self.save()
            return
            
    def end_test_session_setup(self):
        self._handle_code_end(
            self.report.test_session_setup.has_failure() if self.report.test_session_setup else False
        )
    
    def end_test_session_teardown(self):
        self._handle_code_end(
            self.report.test_session_teardown.has_failure() if self.report.test_session_teardown else False
        )
    
    def end_suite_setup(self, testsuite):
        suite_data = self.report.get_suite(testsuite.name)
        self._handle_code_end(
            suite_data.suite_setup.has_failure() if suite_data.suite_setup else False
        )

    def end_suite_teardown(self, testsuite):
        suite_data = self.report.get_suite(testsuite.name)
        self._handle_code_end(
            suite_data.suite_teardown.has_failure() if suite_data.suite_teardown else False
        )
    
    def end_test(self, test, outcome):
        self._handle_code_end(test)
    
    def end_suite(self, testsuite):
        if self.save_mode == SAVE_AT_EACH_TESTSUITE:
            self.save()
    
    def log(self, level, content):
        if self.save_mode == SAVE_AT_EACH_EVENT:
            self.save()
    
    def check(self, description, outcome, details=None):
        if self.save_mode == SAVE_AT_EACH_EVENT:
            self.save()
    
    def end_tests(self):
        self.save()

class FileReportBackend(ReportingBackend):
    def __init__(self, save_mode=SAVE_AT_EACH_FAILED_TEST):
        self.save_mode = save_mode
    
    def serialize_report(self, report, report_dir):
        raise MethodNotImplemented(self, "serialize_report")
    
    def create_reporting_session(self, report, report_dir):
        return FileReportSession(report, report_dir, self, self.save_mode)

def get_available_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend

    return list(filter(lambda b: b.is_available(), [ConsoleBackend(), XmlBackend(), JsonBackend(), HtmlBackend()]))
