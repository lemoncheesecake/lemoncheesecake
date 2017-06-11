'''
Created on Mar 29, 2016

@author: nicolas
'''

import os

from lemoncheesecake.exceptions import MethodNotImplemented, InvalidReportFile,\
    ProgrammingError, method_not_implemented
from lemoncheesecake.utils import object_has_method

__all__ = (
    "get_available_backends", "ReportingBackend", "ReportingSession",
    "save_report", "load_reports_from_dir", "load_report",
    "CAPABILITY_REPORTING_SESSION", "CAPABILITY_SAVE_REPORT", "CAPABILITY_LOAD_REPORT"
)

CAPABILITY_REPORTING_SESSION = 0x1
CAPABILITY_SAVE_REPORT = 0x2
CAPABILITY_LOAD_REPORT = 0x4

SAVE_AT_END_OF_TESTS = 1
SAVE_AT_EACH_TESTSUITE = 2
SAVE_AT_EACH_TEST = 3
SAVE_AT_EACH_FAILED_TEST = 4
SAVE_AT_EACH_EVENT = 5

class ReportingSession:
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

    def end_test(self, test, status):
        pass

    def bypass_test(self, test, status, status_details):
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
        if object_has_method(self, "save_report"):
            capabilities |= CAPABILITY_SAVE_REPORT
        if object_has_method(self, "load_report"):
            capabilities |= CAPABILITY_LOAD_REPORT
        return capabilities

#     def create_reporting_session(self, dir, report):
#         method_not_implemented("create_reporting_session", self)
#
#     def save_report(self, filename, report):
#         method_not_implemented("serialize_report", self)
#
#     def load_report(self, filename):
#         method_not_implemented("unserialize_report", self)

class FileReportSession(ReportingSession):
    def __init__(self, report_filename, report, save_func, save_mode):
        self.report_filename = report_filename
        self.report = report
        self.save_func = save_func
        self.save_mode = save_mode

    def save(self):
        self.save_func(self.report_filename, self.report)

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

    def end_test(self, test, status):
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

    def get_report_filename(self):
        method_not_implemented("get_report_filename", self)

    def create_reporting_session(self, report_dir, report):
        return FileReportSession(
            os.path.join(report_dir, self.get_report_filename()), report, self.save_report, self.save_mode
        )

def get_available_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend

    return list(filter(lambda b: b.is_available(), [ConsoleBackend(), XmlBackend(), JsonBackend(), HtmlBackend()]))

def load_report(filename, backends=None):
    if backends == None:
        backends = get_available_backends()
    for backend in backends:
        if backend.get_capabilities() & CAPABILITY_LOAD_REPORT:
            try:
                return backend.load_report(filename), backend
            except InvalidReportFile:
                pass
    raise InvalidReportFile("Cannot find any suitable report backend to unserialize file '%s'" % filename)

def load_reports_from_dir(dirname, backends=None):
    reports = []
    for filename in [os.path.join(dirname, filename) for filename in os.listdir(dirname)]:
        if os.path.isfile(filename):
            try:
                report, backend = load_report(filename, backends)
                reports.append((report, backend))
            except InvalidReportFile:
                pass
    return reports

def save_report(filename, report, backend):
    if not backend.get_capabilities() & CAPABILITY_SAVE_REPORT:
        raise ProgrammingError("Reporting backend '%s' does not support save operation" % backend.name)
    backend.save_report(filename, report)