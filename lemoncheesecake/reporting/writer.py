'''
Created on Jan 24, 2016

@author: nicolas
'''

import time

from lemoncheesecake.consts import LOG_LEVEL_ERROR
from lemoncheesecake.reporting.report import *
from lemoncheesecake import events

__all__ = "ReportWriter", "initialize_report_writer"


class ReportWriter:
    def __init__(self, report):
        self.report = report
        # pointers to report data parts
        self.current_suite_data = None
        self.current_test_data = None
        self.current_step_data_list = None
        self.current_step_data = None
        # pointers to running test/suite
        self.current_test = None
        self.current_suite = None
        # for test / suite hook / before/after all tests outcome
        self.has_pending_failure = False
        # global status
        self._is_success = True

    def _start_hook(self, ts):
        self.has_pending_failure = False
        hook_data = HookData()
        hook_data.start_time = ts
        return hook_data

    def _end_hook(self, hook_data, ts):
        if hook_data:
            hook_data.end_time = ts
            hook_data.outcome = not self.has_pending_failure

    def end_current_step(self, ts):
        if self.current_step_data:
            self.current_step_data.end_time = ts
            self.current_step_data = None

        # remove previous step from report data if it was empty
        if self.current_step_data_list and len(self.current_step_data_list[-1].entries) == 0:
            del self.current_step_data_list[-1]

    def on_test_session_start(self, event):
        self.report.start_time = event.time

    def on_test_session_end(self, event):
        self.report.end_time = event.time
        self.report.report_generation_time = self.report.end_time

    def on_test_session_setup_start(self, event):
        self.report.test_session_setup = self._start_hook(event.time)
        self.current_step_data_list = self.report.test_session_setup.steps

    def on_test_session_setup_end(self, event):
        if self.report.test_session_setup.is_empty():
            self.report.test_session_setup = None
        else:
            self._end_hook(self.report.test_session_setup, event.time)
            self.end_current_step(event.time)

    def on_test_session_teardown_start(self, event):
        self.report.test_session_teardown = self._start_hook(event.time)
        self.current_step_data_list = self.report.test_session_teardown.steps

    def on_test_session_teardown_end(self, event):
        if self.report.test_session_teardown.is_empty():
            self.report.test_session_teardown = None
        else:
            self._end_hook(self.report.test_session_teardown, event.time)
            self.end_current_step(event.time)

    def on_suite_start(self, event):
        suite = event.suite
        self.current_suite = suite
        suite_data = SuiteData(suite.name, suite.description)
        suite_data.tags.extend(suite.tags)
        suite_data.properties.update(suite.properties)
        suite_data.links.extend(suite.links)
        if self.current_suite_data:
            self.current_suite_data.add_suite(suite_data)
        else:
            self.report.add_suite(suite_data)
        self.current_suite_data = suite_data

    def on_suite_setup_start(self, event):
        self.current_suite_data.suite_setup = self._start_hook(event.time)
        self.current_step_data_list = self.current_suite_data.suite_setup.steps

    def on_suite_setup_end(self, event):
        if self.current_suite_data.suite_setup.is_empty():
            self.current_suite_data.suite_setup = None
        else:
            self._end_hook(self.current_suite_data.suite_setup, event.time)
            self.end_current_step(event.time)

    def on_suite_teardown_start(self, event):
        self.current_suite_data.suite_teardown = self._start_hook(event.time)
        self.current_step_data_list = self.current_suite_data.suite_teardown.steps

    def on_suite_teardown_end(self, event):
        if self.current_suite_data.suite_teardown.is_empty():
            self.current_suite_data.suite_teardown = None
        else:
            self.end_current_step(event.time)
            self._end_hook(self.current_suite_data.suite_teardown, event.time)

    def on_suite_end(self, event):
        self.current_suite_data = self.current_suite_data.parent_suite
        self.current_suite = self.current_suite.parent_suite

    def on_test_start(self, event):
        test = event.test
        self.has_pending_failure = False
        self.current_test = test
        self.current_test_data = TestData(test.name, test.description)
        self.current_test_data.tags.extend(test.tags)
        self.current_test_data.properties.update(test.properties)
        self.current_test_data.links.extend(test.links)
        self.current_test_data.start_time = event.time
        self.current_suite_data.add_test(self.current_test_data)
        self.current_step_data_list = self.current_test_data.steps

    def on_test_end(self, event):
        self.current_test_data.status = event.test_status
        self.current_test_data.end_time = event.time
        self.end_current_step(event.time)

        self.current_test = None
        self.current_test_data = None
        self.current_step_data_list = None

    def _bypass_test(self, test, status, status_details, time):
        test_data = TestData(test.name, test.description)
        test_data.tags.extend(test.tags)
        test_data.properties.update(test.properties)
        test_data.links.extend(test.links)
        test_data.end_time = test_data.start_time = time
        test_data.status = status
        test_data.status_details = status_details
        self.current_suite_data.add_test(test_data)

    def on_test_skipped(self, event):
        self._is_success = False
        self._bypass_test(event.test, "skipped", event.skipped_reason, event.time)

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled", "", event.time)

    def on_step(self, event):
        self.end_current_step(event.time)

        self.current_step_data = StepData(event.step_description)
        self.current_step_data.start_time = event.time

        self.current_step_data_list.append(self.current_step_data)

    def on_log(self, event):
        if event.log_level == LOG_LEVEL_ERROR:
            self._is_success = False
            self.has_pending_failure = True
        self.current_step_data.entries.append(LogData(event.log_level, event.log_message, event.time))

    def on_check(self, event):
        self.current_step_data.entries.append(
            CheckData(event.check_description, event.check_outcome, event.check_details)
        )

        if event.check_outcome is False:
            self._is_success = False
            self.has_pending_failure = True

    def on_log_attachment(self, event):
        self.current_step_data.entries.append(AttachmentData(event.attachment_description, event.attachment_path))

    def on_log_url(self, event):
        self.current_step_data.entries.append(UrlData(event.url_description, event.url))

    def is_successful(self):
        return self._is_success


def initialize_report_writer(report):
    writer = ReportWriter(report)
    events.add_listener(writer)
    return writer
