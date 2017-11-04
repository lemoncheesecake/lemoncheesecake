'''
Created on Jan 24, 2016

@author: nicolas
'''

import time

from lemoncheesecake.consts import LOG_LEVEL_ERROR
from lemoncheesecake.reporting.report import *
from lemoncheesecake import events

__all__ = "ReportWriter", "initialize_report_writer"


def _set_step(description, step_time=None):
    events.fire("on_step", description, event_time=step_time)


class ReportWriter:
    def __init__(self, report):
        self.report = report
        self.default_step_description = None
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

    def on_tests_beginning(self, report, start_time):
        self.report.start_time = start_time

    def on_tests_ending(self, report, end_time):
        self.report.end_time = end_time
        self.report.report_generation_time = self.report.end_time

    def on_test_session_setup_beginning(self, time):
        self.report.test_session_setup = self._start_hook(time)
        self.current_step_data_list = self.report.test_session_setup.steps
        self.default_step_description = "Setup test session"

    def on_test_session_setup_ending(self, outcome, time):
        if self.report.test_session_setup.is_empty():
            self.report.test_session_setup = None
        else:
            self._end_hook(self.report.test_session_setup, time)
            self.end_current_step(time)

    def on_test_session_teardown_beginning(self, time):
        self.report.test_session_teardown = self._start_hook(time)
        self.current_step_data_list = self.report.test_session_teardown.steps
        self.default_step_description = "Teardown test session"

    def on_test_session_teardown_ending(self, outcome, time):
        if self.report.test_session_teardown.is_empty():
            self.report.test_session_teardown = None
        else:
            self._end_hook(self.report.test_session_teardown, time)
            self.end_current_step(time)

    def on_suite_beginning(self, suite):
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

    def on_suite_setup_beginning(self, suite, time):
        self.current_suite_data.suite_setup = self._start_hook(time)
        self.current_step_data_list = self.current_suite_data.suite_setup.steps
        self.default_step_description = "Setup suite"

    def on_suite_setup_ending(self, suite, outcome, time):
        if self.current_suite_data.suite_setup.is_empty():
            self.current_suite_data.suite_setup = None
        else:
            self._end_hook(self.current_suite_data.suite_setup, time)
            self.end_current_step(time)

    def on_suite_teardown_beginning(self, suite, time):
        self.current_suite_data.suite_teardown = self._start_hook(time)
        self.current_step_data_list = self.current_suite_data.suite_teardown.steps
        self.default_step_description = "Teardown suite"

    def on_suite_teardown_ending(self, suite, outcome, time):
        if self.current_suite_data.suite_teardown.is_empty():
            self.current_suite_data.suite_teardown = None
        else:
            self.end_current_step(time)
            self._end_hook(self.current_suite_data.suite_teardown, time)

    def on_suite_ending(self, suite):
        self.current_suite_data = self.current_suite_data.parent_suite
        self.current_suite = self.current_suite.parent_suite

    def on_test_beginning(self, test, start_time):
        self.has_pending_failure = False
        self.current_test = test
        self.current_test_data = TestData(test.name, test.description)
        self.current_test_data.tags.extend(test.tags)
        self.current_test_data.properties.update(test.properties)
        self.current_test_data.links.extend(test.links)
        self.current_test_data.start_time = start_time
        self.current_suite_data.add_test(self.current_test_data)
        self.current_step_data_list = self.current_test_data.steps
        self.default_step_description = test.description

    def on_test_setup_beginning(self, test):
        _set_step("Setup test")

    def on_test_setup_ending(self, test, outcome):
        _set_step(self.current_test.description)

    def on_test_teardown_beginning(self, test):
        _set_step("Teardown test")

    def on_test_teardown_ending(self, test, outcome):
        pass

    def on_test_ending(self, test, status, end_time):
        self.current_test_data.status = status
        self.current_test_data.end_time = end_time
        self.end_current_step(end_time)

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

    def on_skipped_test(self, test, reason, time):
        self._is_success = False
        self._bypass_test(test, "skipped", reason, time)

    def on_disabled_test(self, test, time):
        self._bypass_test(test, "disabled", "", time)

    def create_step_if_needed(self, step_time=None):
        if not self.current_step_data_list:
            _set_step(self.default_step_description, step_time or time.time())

    def on_step(self, description, step_time):
        self.end_current_step(step_time)

        self.current_step_data = StepData(description)
        self.current_step_data.start_time = step_time

        self.current_step_data_list.append(self.current_step_data)

    def on_log(self, level, content, log_time):
        if level == LOG_LEVEL_ERROR:
            self._is_success = False
            self.has_pending_failure = True
        self.create_step_if_needed(log_time)
        self.current_step_data.entries.append(LogData(level, content, log_time))

    def on_check(self, description, outcome, details):
        self.create_step_if_needed()
        self.current_step_data.entries.append(CheckData(description, outcome, details))

        if outcome is False:
            self._is_success = False
            self.has_pending_failure = True

    def on_log_attachment(self, path, description):
        self.create_step_if_needed()
        self.current_step_data.entries.append(AttachmentData(description, path))

    def on_log_url(self, url, description):
        self.create_step_if_needed()
        self.current_step_data.entries.append(UrlData(description, url))

    def is_successful(self):
        return self._is_success


def initialize_report_writer(report):
    writer = ReportWriter(report)
    events.add_listener(writer)
    return writer
