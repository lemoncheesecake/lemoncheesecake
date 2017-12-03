from __future__ import print_function

import os
import sys
import traceback
import mimetypes

try:
    from reportportal_client import ReportPortalServiceAsync
    REPORT_PORTAL_CLIENT_IS_AVAILABLE = True
except ImportError:
    REPORT_PORTAL_CLIENT_IS_AVAILABLE = False

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.exceptions import UserError


def make_time(t):
    return str(int(t * 1000))


def convert_properties_into_tags(props):
    return ["%s_%s" % (name, value) for name, value in props.items()]


def convert_links_into_tags(links):
    return [link[1] or link[0] for link in links]


class ReportPortalReportingSession(ReportingSession):
    def __init__(self, url, auth_token, project, launch_name, launch_description, report_dir, report):
        self.service = ReportPortalServiceAsync(
            endpoint=url, project=project, token=auth_token, error_handler=self._handle_rp_error
        )
        self.launch_name = launch_name
        self.launch_description = launch_description
        self.report_dir = report_dir
        self.report = report
        self._rp_exc_info = None
        self._current_suite_test_statuses = []

    def _handle_rp_error(self, exc_info):
        self._rp_exc_info = exc_info
        return False  # stop on error

    def _has_rp_error(self):
        return self._rp_exc_info is not None

    def _show_rp_error(self):
        print(
            "Got the following exception using ReportPortal, "
            "test results have not been properly synced:",
            file=sys.stderr
        )
        traceback.print_exception(*self._rp_exc_info, file=sys.stderr)

    def _end_current_test_item(self, end_time, status):
        self.service.finish_test_item(end_time=make_time(end_time), status=status)

    def _start_test_item(self, item_type, start_time, name, description, wrapped=False):
        if wrapped:
            self.service.start_test_item(
                item_type="SUITE", start_time=make_time(start_time),
                name=name, description=description
            )
        self.service.start_test_item(
            item_type=item_type, start_time=make_time(start_time),
            name=name, description=description
        )

    def _end_test_item(self, end_time, outcome, wrapped=False):
        status = "passed" if outcome else "failed"
        if wrapped:
            self._end_current_test_item(end_time, status=status)
        self._end_current_test_item(end_time, status=status)

    def on_tests_beginning(self, report, start_time):
        if self._has_rp_error():
            return

        self.service.start_launch(
            name=self.launch_name, description=self.launch_description, start_time=make_time(start_time)
        )

    def on_tests_ending(self, report, end_time):
        if self._has_rp_error():
            self._show_rp_error()
        else:
            self.service.finish_launch(end_time=make_time(end_time))
            self.service.terminate()

            if self._has_rp_error():
                self._show_rp_error()

    def on_test_session_setup_beginning(self, start_time):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="BEFORE_CLASS", start_time=start_time,
            name="session_setup", description="Test Session Setup",
            wrapped=True
        )

    def on_test_session_setup_ending(self, outcome, end_time):
        if self._has_rp_error():
            return

        self._end_test_item(end_time, outcome, wrapped=True)

    def on_test_session_teardown_beginning(self, start_time):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="AFTER_CLASS", start_time=start_time,
            name="session_teardown", description="Test Session Teardown",
            wrapped=True
        )

    def on_test_session_teardown_ending(self, outcome, end_time):
        if self._has_rp_error():
            return

        self._end_test_item(end_time, outcome, wrapped=True)

    def on_suite_beginning(self, suite, start_time):
        if self._has_rp_error():
            return

        self.service.start_test_item(
            item_type="SUITE", start_time=make_time(start_time),
            name=suite.name, description=suite.description,
            tags=suite.tags +
                convert_properties_into_tags(suite.properties) +
                convert_links_into_tags(suite.links),
        )

    def on_suite_ending(self, suite, end_time):
        if self._has_rp_error():
            return

        self._end_current_test_item(end_time, status="passed")

    def on_suite_setup_beginning(self, suite, start_time):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="BEFORE_CLASS", start_time=start_time,
            name="suite_setup", description="Suite Setup",
            wrapped=len(suite.get_suites()) > 0
        )

    def on_suite_setup_ending(self, suite, outcome, end_time):
        if self._has_rp_error():
            return

        self._end_test_item(end_time, outcome=outcome, wrapped=len(suite.get_suites()) > 0)

    def on_suite_teardown_beginning(self, suite, start_time):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="AFTER_CLASS", start_time=start_time,
            name="suite_teardown", description="Suite Teardown",
            wrapped=len(suite.get_suites()) > 0
        )

    def on_suite_teardown_ending(self, suite, outcome, end_time):
        if self._has_rp_error():
            return

        self._end_test_item(end_time, outcome=outcome, wrapped=len(suite.get_suites()) > 0)

    def on_test_beginning(self, test, start_time):
        if self._has_rp_error():
            return

        self.service.start_test_item(
            item_type="TEST", start_time=make_time(start_time),
            name=test.name, description=test.description,
            tags=test.tags +
                 convert_properties_into_tags(test.properties) +
                 convert_links_into_tags(test.links)
        )

    def on_test_ending(self, test, status, end_time):
        if self._has_rp_error():
            return

        self._end_current_test_item(end_time, status)

    def _bypass_test(self, test, status, time):
        if self._has_rp_error():
            return

        self.service.start_test_item(
            item_type="TEST", start_time=make_time(time),
            name=test.name, description=test.description, tags=test.tags,
        )
        self._end_current_test_item(time, status=status)

    def on_skipped_test(self, test, reason, time):
        if self._has_rp_error():
            return

        self._bypass_test(test, "skipped", time)

    def on_disabled_test(self, test, time):
        # do not log disabled test, moreover it seems that the is not corresponding status in ReportPortal
        pass

    def on_step(self, description, start_time):
        if self._has_rp_error():
            return

        self.service.log(make_time(start_time), "--- STEP: %s ---" % description, "INFO")

    def on_log(self, level, content, log_time):
        if self._has_rp_error():
            return

        self.service.log(make_time(log_time), content, level)

    def on_check(self, description, outcome, details, check_time):
        if self._has_rp_error():
            return

        message = "%s => %s" % (description, "OK" if outcome else "NOT OK")
        if details is not None:
            message += "\nDetails: %s" % details
        self.service.log(make_time(check_time), message, "INFO" if outcome else "ERROR")

    def on_log_attachment(self, path, filename, description, log_time):
        if self._has_rp_error():
            return

        abspath = os.path.join(self.report_dir, path)
        with open(abspath, "rb") as fh:
            self.service.log(make_time(log_time), description, "INFO", attachment={
                "name": filename,
                "data": fh.read(),
                "mime": mimetypes.guess_type(abspath)[0] or "application/octet-stream"
            })

    def on_log_url(self, url, description, log_time):
        if self._has_rp_error():
            return

        if description and description != url:
            message = "%s: %s" % (description, url)
        else:
            message = url
        self.service.log(make_time(log_time), message, "INFO")


class ReportPortalBackend(ReportingBackend):
    name = "reportportal"

    def is_available(self):
        return REPORT_PORTAL_CLIENT_IS_AVAILABLE

    def create_reporting_session(self, report_dir, report):
        try:
            url = os.environ["RP_URL"]
            auth_token = os.environ["RP_AUTH_TOKEN"]
            project = os.environ["RP_PROJECT"]
            launch_name = os.environ.get("RP_LAUNCH_NAME", "Test Run")
            launch_description = os.environ.get("RP_LAUNCH_DESCRIPTION", None)
        except KeyError as excp:
            raise UserError("ReportPortal reporting backend, cannot get environment variable %s" % excp)

        return ReportPortalReportingSession(
            url, auth_token, project, launch_name, launch_description, report_dir, report
        )
