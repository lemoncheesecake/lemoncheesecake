'''
Created on Mar 29, 2016

@author: nicolas
'''

import os
import os.path as osp

from lemoncheesecake.exceptions import InvalidReportFile, ProgrammingError
from lemoncheesecake.reporting.report import Report


class ReportingSession(object):
    pass


class ReportingSessionBuilderMixin(object):
    def create_reporting_session(self, report_dir, report, parallel, report_saving_strategy):
        raise NotImplemented()


class ReportSerializerMixin(object):
    def save_report(self, filename, report):
        raise NotImplemented()


class ReportUnserializerMixin(object):
    def load_report(self, filename):
        raise NotImplemented()


class ReportingBackend(object):
    def get_name(self):
        raise NotImplemented()

    def is_available(self):
        return True


class FileReportSession(ReportingSession):
    def __init__(self, report_filename, report, reporting_backend, report_saving_strategy):
        self.report_filename = report_filename
        self.report = report
        self.reporting_backend = reporting_backend
        self.report_saving_strategy = report_saving_strategy

    def _save(self):
        self.reporting_backend.save_report(self.report_filename, self.report)

    def _handle_event(self, event):
        report_must_be_saved = self.report_saving_strategy and self.report_saving_strategy(event, self.report)
        if report_must_be_saved:
            self._save()

    on_test_session_setup_end = _handle_event
    on_test_session_teardown_end = _handle_event
    on_suite_setup_end = _handle_event
    on_suite_teardown_end = _handle_event
    on_test_end = _handle_event
    on_suite_end = _handle_event
    on_log = _handle_event
    on_log_attachment = _handle_event
    on_log_url = _handle_event
    on_check = _handle_event

    def on_test_session_end(self, event):
        # no matter what is the report_saving_strategy,
        # the report will always be saved at the end of tests
        self._save()


class FileReportBackend(ReportingBackend, ReportSerializerMixin, ReportingSessionBuilderMixin):
    def get_report_filename(self):
        raise NotImplemented()

    def create_reporting_session(self, report_dir, report, parallel, report_saving_strategy):
        return FileReportSession(
            os.path.join(report_dir, self.get_report_filename()), report, self, report_saving_strategy
        )


def filter_available_reporting_backends(backends):
    return list(filter(lambda backend: backend.is_available(), backends))


def get_reporting_backends():
    from lemoncheesecake.reporting.backends import REPORTING_BACKENDS
    return list(
        filter(
            lambda backend: backend.is_available(),
            (backend_class() for backend_class in REPORTING_BACKENDS)
        )
    )


class BoundReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.backend = None
        self.path = None

    def bind(self, backend, path):
        self.backend = backend
        self.path = path
        return self

    def is_bound(self):
        return self.backend is not None and self.path is not None

    def save(self):
        if not self.is_bound():
            raise ProgrammingError("Cannot save unbound report")
        save_report(self.path, self, self.backend)


def load_report_from_file(filename, backends=None):
    if backends is None:
        backends = get_reporting_backends()
    for backend in backends:
        if isinstance(backend, ReportUnserializerMixin):
            try:
                return backend.load_report(filename)
            except IOError as excp:
                raise InvalidReportFile("Cannot load report from file '%s': %s" % (filename, excp))
            except InvalidReportFile:
                pass
    raise InvalidReportFile("Cannot find any suitable report backend to load report file '%s'" % filename)


def load_reports_from_dir(dirname, backends=None):
    for filename in [os.path.join(dirname, filename) for filename in os.listdir(dirname)]:
        if os.path.isfile(filename):
            try:
                yield load_report_from_file(filename, backends)
            except InvalidReportFile:
                pass


def load_report(path, backends=None):
    if osp.isdir(path):
        try:
            return next(load_reports_from_dir(path, backends))
        except StopIteration:
            raise InvalidReportFile("Cannot find any report in directory '%s'" % path)
    else:
        return load_report_from_file(path, backends)


def save_report(filename, report, backend):
    if not isinstance(backend, ReportSerializerMixin):
        raise ProgrammingError("Reporting backend '%s' does not support report saving" % backend.get_name())
    backend.save_report(filename, report)
