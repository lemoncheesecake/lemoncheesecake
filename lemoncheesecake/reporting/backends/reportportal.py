from __future__ import print_function

import os
import os.path as osp
import sys
import traceback
import mimetypes

try:
    import reportportal_client
    REPORT_PORTAL_CLIENT_IS_AVAILABLE = True
except ImportError:
    REPORT_PORTAL_CLIENT_IS_AVAILABLE = False

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession, ReportingSessionBuilderMixin
from lemoncheesecake.exceptions import UserError
from lemoncheesecake.events import SyncEventManager
from lemoncheesecake.reporting.replay import replay_report_events


def make_time(t):
    return str(int(t * 1000))


def make_tags_from_test_tree_node(node):
    return node.tags + \
           ["%s_%s" % (name, value) for name, value in node.properties.items()] + \
           [link[1] or link[0] for link in node.links]


class ReportPortalReportingSession(ReportingSession):
    def __init__(self, url, auth_token, project, launch_name, launch_description, report_dir, report):
        self.service = reportportal_client.ReportPortalServiceAsync(
            endpoint=url, project=project, token=auth_token, error_handler=self._handle_rp_error
        )
        self.launch_name = launch_name
        self.launch_description = launch_description
        self.report_dir = report_dir
        self.report = report
        self._rp_exc_info = None

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

    def _end_test_item(self, end_time, is_successful, wrapped=False):
        status = "passed" if is_successful else "failed"
        if wrapped:
            self._end_current_test_item(end_time, status=status)
        self._end_current_test_item(end_time, status=status)

    def on_test_session_start(self, event):
        if self._has_rp_error():
            return

        self.service.start_launch(
            name=self.launch_name, description=self.launch_description, start_time=make_time(event.time)
        )

    def on_test_session_end(self, event):
        if self._has_rp_error():
            self._show_rp_error()
        else:
            self.service.finish_launch(end_time=make_time(event.time))
            self.service.terminate()

            if self._has_rp_error():
                self._show_rp_error()

    def on_test_session_setup_start(self, event):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="BEFORE_CLASS", start_time=event.time,
            name="session_setup", description="Test Session Setup",
            wrapped=True
        )

    def on_test_session_setup_end(self, event):
        if self._has_rp_error():
            return

        self._end_test_item(
            event.time,
            not self.report.test_session_setup or self.report.test_session_setup.is_successful(),
            wrapped=True
        )

    def on_test_session_teardown_start(self, event):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="AFTER_CLASS", start_time=event.time,
            name="session_teardown", description="Test Session Teardown",
            wrapped=True
        )

    def on_test_session_teardown_end(self, event):
        if self._has_rp_error():
            return

        self._end_test_item(
            event.time,
            not self.report.test_session_teardown or self.report.test_session_teardown.is_successful(),
            wrapped=True
        )

    def on_suite_start(self, event):
        if self._has_rp_error():
            return

        suite = event.suite
        self.service.start_test_item(
            item_type="SUITE", start_time=make_time(event.time),
            name=suite.name, description=suite.description,
            tags=make_tags_from_test_tree_node(suite)
        )

    def on_suite_end(self, event):
        if self._has_rp_error():
            return

        self._end_current_test_item(event.time, status="passed")

    def on_suite_setup_start(self, event):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="BEFORE_CLASS", start_time=event.time,
            name="suite_setup", description="Suite Setup",
            wrapped=len(event.suite.get_suites()) > 0
        )

    def on_suite_setup_end(self, event):
        if self._has_rp_error():
            return

        suite_data = self.report.get_suite(event.suite)

        self._end_test_item(
            event.time,
            not suite_data.suite_setup or suite_data.suite_setup.is_successful(),
            wrapped=len(event.suite.get_suites()) > 0
        )

    def on_suite_teardown_start(self, event):
        if self._has_rp_error():
            return

        self._start_test_item(
            item_type="AFTER_CLASS", start_time=event.time,
            name="suite_teardown", description="Suite Teardown",
            wrapped=len(event.suite.get_suites()) > 0
        )

    def on_suite_teardown_end(self, event):
        if self._has_rp_error():
            return

        suite_data = self.report.get_suite(event.suite)

        self._end_test_item(
            event.time,
            not suite_data.suite_teardown or suite_data.suite_teardown.is_successful(),
            wrapped=len(event.suite.get_suites()) > 0
        )

    def on_test_start(self, event):
        if self._has_rp_error():
            return

        test = event.test
        self.service.start_test_item(
            item_type="TEST", start_time=make_time(event.time),
            name=test.name, description=test.description,
            tags=make_tags_from_test_tree_node(test)
        )

    def on_test_end(self, event):
        if self._has_rp_error():
            return

        test_data = self.report.get_test(event.test)
        self._end_current_test_item(event.time, test_data.status)

    def _bypass_test(self, test, status, time):
        if self._has_rp_error():
            return

        self.service.start_test_item(
            item_type="TEST", start_time=make_time(time),
            name=test.name, description=test.description, tags=test.tags,
        )
        self._end_current_test_item(time, status=status)

    def on_test_skipped(self, event):
        if self._has_rp_error():
            return

        self._bypass_test(event.test, "skipped", event.time)

    def on_disabled_test(self, event):
        # do not log disabled test, moreover it seems that there is not corresponding status in ReportPortal
        pass

    def on_step_start(self, event):
        if self._has_rp_error():
            return

        self.service.log(make_time(event.time), "--- STEP: %s ---" % event.step_description, "INFO")

    def on_log(self, event):
        if self._has_rp_error():
            return

        self.service.log(make_time(event.time), event.log_message, event.log_level.upper())

    def on_check(self, event):
        if self._has_rp_error():
            return

        message = "%s => %s" % (event.check_description, "OK" if event.check_is_successful else "NOT OK")
        if event.check_details is not None:
            message += "\nDetails: %s" % event.check_details
        self.service.log(make_time(event.time), message, "INFO" if event.check_is_successful else "ERROR")

    def on_log_attachment(self, event):
        if self._has_rp_error():
            return

        abspath = os.path.join(self.report_dir, event.attachment_path)
        with open(abspath, "rb") as fh:
            self.service.log(make_time(event.time), event.attachment_description, "INFO", attachment={
                "name": osp.basename(event.attachment_path),
                "data": fh.read(),
                "mime": mimetypes.guess_type(abspath)[0] or "application/octet-stream"
            })

    def on_log_url(self, event):
        if self._has_rp_error():
            return

        if event.url_description and event.url_description != event.url:
            message = "%s: %s" % (event.url_description, event.url)
        else:
            message = event.url
        self.service.log(make_time(event.time), message, "INFO")


class ReportPortalReportingSessionParallelized(ReportingSession):
    def __init__(self, *args):
        self._session = ReportPortalReportingSession(*args)

    def on_test_session_end(self, _):
        event_manager = SyncEventManager.load()
        event_manager.add_listener(self._session)
        replay_report_events(self._session.report, event_manager)


class ReportPortalBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def get_name(self):
        return "reportportal"

    def is_available(self):
        return REPORT_PORTAL_CLIENT_IS_AVAILABLE

    def create_reporting_session(self, report_dir, report, parallel, _):
        try:
            url = os.environ["LCC_RP_URL"]
            auth_token = os.environ["LCC_RP_AUTH_TOKEN"]
            project = os.environ["LCC_RP_PROJECT"]
            launch_name = os.environ.get("LCC_RP_LAUNCH_NAME", "Test Run")
            launch_description = os.environ.get("LCC_RP_LAUNCH_DESCRIPTION", None)
        except KeyError as excp:
            raise UserError("ReportPortal reporting backend, cannot get environment variable %s" % excp)

        # the ReportPortal REST API allows working on multiple test item at a time,
        # unfortunately reportportal_client module does not support it because test item ids are not exposed and
        # the API make it impossible to work on multiple test item in parallel.
        # When lemoncheesecake tests are run in parallel, we must then wait the end of the test session to
        # replay the events from the report as the tests would have been run sequentially.
        if parallel:
            return ReportPortalReportingSessionParallelized(
                url, auth_token, project, launch_name, launch_description, report_dir, report
            )
        else:
            return ReportPortalReportingSession(
                url, auth_token, project, launch_name, launch_description, report_dir, report
            )
