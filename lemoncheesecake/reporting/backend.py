'''
Created on Mar 29, 2016

@author: nicolas
'''

import os

from lemoncheesecake.helpers.orderedset import OrderedSet
from lemoncheesecake.exceptions import LemoncheesecakeException

_NEGATION_FLAGS = "-^~"


class ReportingSession(object):
    pass


class ReportingSessionBuilderMixin(object):
    def create_reporting_session(self, report_dir, report, parallel, report_saving_strategy):
        raise NotImplementedError()


class ReportSerializerMixin(object):
    def save_report(self, filename, report):
        raise NotImplementedError()


class ReportUnserializerMixin(object):
    def load_report(self, filename):
        raise NotImplementedError()


class ReportingBackend(object):
    def get_name(self):
        raise NotImplementedError()

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
        raise NotImplementedError()

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


def get_reporting_backend_names(default_names, custom_names):
    if all(name[0] not in ("+" + _NEGATION_FLAGS) for name in custom_names):  # fixed list
        return custom_names

    elif all(name[0] in ("+" + _NEGATION_FLAGS) for name in custom_names):  # turn on/off directives
        names = OrderedSet(default_names)
        for specified_name in custom_names:
            if specified_name[0] == "+":  # turn on
                names.add(specified_name[1:])
            else:  # turn off
                try:
                    names.remove(specified_name[1:])
                except KeyError:
                    raise ValueError(
                        "reporting backend '%s' is not among the default reporting backends" % specified_name[1:]
                    )
        return names

    else:
        raise ValueError(
            "either the custom reporting backends must be fixed backend list, "
            "or a list of turn on/off (+ / ^) directives"
        )


def parse_reporting_backend_names_expression(expr):
    return list(filter(bool, expr.split(" ")))


def get_reporting_backend_by_name(name):
    try:
        return next(backend for backend in get_reporting_backends() if backend.get_name() == name)
    except StopIteration:
        raise KeyError()


def get_reporting_backends_for_test_run(available_backends, backend_names):
    backends = []
    for backend_name in backend_names:
        try:
            backend = available_backends[backend_name]
        except KeyError:
            raise LemoncheesecakeException("Unknown reporting backend '%s'" % backend_name)
        if not isinstance(backend, ReportingSessionBuilderMixin):
            raise LemoncheesecakeException("Reporting backend '%s' is not suitable for test run" % backend_name)
        backends.append(backend)
    return backends
