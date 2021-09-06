'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.reporting.report import \
    SuiteResult, TestResult, Result, Step, Log, Check, Attachment, Url


class ReportWriter:
    def __init__(self, report):
        self.report = report
        self.active_steps = {}

    def _get_test_result(self, test):
        return self.report.get_test(test)

    def _get_suite_result(self, suite):
        return self.report.get_suite(suite)

    def _add_step_log(self, log, event):
        result = self.report.get(event.location)
        assert result, "Cannot find location %s in the report" % event.location
        step = self._lookup_step(event)
        assert step, "Cannot find active step for %s" % event.location
        assert not step.end_time, "Cannot update step '%s', it has already been ended" % step.description
        step.add_log(log)

    @staticmethod
    def _initialize_result(start_time):
        result = Result()
        result.start_time = start_time
        return result

    @staticmethod
    def _initialize_test_result(test, start_time):
        result = TestResult(test.name, test.description)
        result.tags.extend(test.tags)
        result.properties.update(test.properties)
        result.links.extend(test.links)
        result.rank = test.rank
        result.start_time = start_time
        return result

    @staticmethod
    def _finalize_result(result, end_time):
        result.end_time = end_time
        result.status = "passed" if result.is_successful() else "failed"

    def _lookup_step(self, event):
        try:
            return self.active_steps[event.thread_id]
        except KeyError:
            return None

    def on_test_session_start(self, event):
        self.report.start_time = event.time

    def on_test_session_end(self, event):
        self.report.end_time = event.time

    def on_test_session_setup_start(self, event):
        self.report.test_session_setup = self._initialize_result(event.time)

    def on_test_session_setup_end(self, event):
        self._finalize_result(self.report.test_session_setup, event.time)

    def on_test_session_teardown_start(self, event):
        self.report.test_session_teardown = self._initialize_result(event.time)

    def on_test_session_teardown_end(self, event):
        self._finalize_result(self.report.test_session_teardown, event.time)

    def on_suite_start(self, event):
        suite = event.suite
        suite_result = SuiteResult(suite.name, suite.description)
        suite_result.start_time = event.time
        suite_result.tags.extend(suite.tags)
        suite_result.properties.update(suite.properties)
        suite_result.links.extend(suite.links)
        suite_result.rank = suite.rank
        if suite.parent_suite:
            parent_suite_result = self._get_suite_result(suite.parent_suite)
            parent_suite_result.add_suite(suite_result)
        else:
            self.report.add_suite(suite_result)

    def on_suite_end(self, event):
        suite_result = self._get_suite_result(event.suite)
        suite_result.end_time = event.time

    def on_suite_setup_start(self, event):
        suite_result = self._get_suite_result(event.suite)
        suite_result.suite_setup = self._initialize_result(event.time)

    def on_suite_setup_end(self, event):
        suite_result = self._get_suite_result(event.suite)
        self._finalize_result(suite_result.suite_setup, event.time)

    def on_suite_teardown_start(self, event):
        suite_result = self._get_suite_result(event.suite)
        suite_result.suite_teardown = self._initialize_result(event.time)

    def on_suite_teardown_end(self, event):
        suite_result = self._get_suite_result(event.suite)
        self._finalize_result(suite_result.suite_teardown, event.time)

    def on_test_start(self, event):
        test_result = self._initialize_test_result(event.test, event.time)
        suite_result = self._get_suite_result(event.test.parent_suite)
        suite_result.add_test(test_result)

    def on_test_end(self, event):
        test_result = self._get_test_result(event.test)
        self._finalize_result(test_result, event.time)

    def _bypass_test(self, test, status, status_details, time):
        test_result = self._initialize_test_result(test, time)
        test_result.end_time = time
        test_result.status = status
        test_result.status_details = status_details

        suite_result = self._get_suite_result(test.parent_suite)
        suite_result.add_test(test_result)

    def on_test_skipped(self, event):
        self._bypass_test(event.test, "skipped", event.skipped_reason, event.time)

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled", event.disabled_reason, event.time)

    def on_step_start(self, event):
        result = self.report.get(event.location)
        step = Step(event.step_description)
        step.start_time = event.time
        result.add_step(step)
        self.active_steps[event.thread_id] = step

    def on_step_end(self, event):
        step = self._lookup_step(event)
        step.end_time = event.time

    def on_log(self, event):
        self._add_step_log(
            Log(event.log_level, event.log_message, event.time), event
        )

    def on_check(self, event):
        self._add_step_log(
            Check(event.check_description, event.check_is_successful, event.check_details, event.time), event
        )

    def on_log_attachment(self, event):
        self._add_step_log(
            Attachment(event.attachment_description, event.attachment_path, event.as_image, event.time), event
        )

    def on_log_url(self, event):
        self._add_step_log(
            Url(event.url_description, event.url, event.time), event
        )
