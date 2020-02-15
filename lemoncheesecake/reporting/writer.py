'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.reporting.report import \
    SuiteResult, TestResult, Result, Step, Log, Check, Attachment, Url
from lemoncheesecake.exceptions import ProgrammingError


class ReportWriter:
    def __init__(self, report):
        self.report = report

    def _get_test_result(self, test):
        return self.report.get_test(test)

    def _get_suite_result(self, suite):
        return self.report.get_suite(suite)

    def _add_step_entry(self, entry, event):
        result = self.report.get(event.location)
        if not result:
            raise ProgrammingError("Cannot find location %s in the report" % event.location)
        step = self._lookup_step(result.get_steps(), event.step)
        if step.end_time:
            raise ProgrammingError("Cannot update step '%s', it is already ended" % step.description)
        step.entries.append(entry)

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
        for step in result.get_steps():
            if step.end_time is None:
                step.end_time = end_time

        result.end_time = end_time
        result.status = "passed" if result.is_successful() else "failed"

    @staticmethod
    def _lookup_step(steps, step):
        if step is None:
            return steps[-1]
        else:
            try:
                return next(s for s in reversed(steps) if s.description == step)
            except StopIteration:
                raise ProgrammingError("Cannot find step '%s'" % step)

    @staticmethod
    def _lookup_current_step(steps):
        for step in reversed(steps):
            if not step._detached:
                return step
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

    def on_step(self, event):
        result = self.report.get(event.location)
        current_step = self._lookup_current_step(result.get_steps())
        if current_step:
            current_step.end_time = event.time

        new_step = Step(event.step_description, detached=event.detached)
        new_step.start_time = event.time
        result.add_step(new_step)

    def on_step_end(self, event):
        result = self.report.get(event.location)
        step = self._lookup_step(result.get_steps(), event.step)

        # only detached steps can be explicitly ended, otherwise do nothing
        if step._detached:
            step.end_time = event.time

    def on_log(self, event):
        self._add_step_entry(
            Log(event.log_level, event.log_message, event.time), event
        )

    def on_check(self, event):
        self._add_step_entry(
            Check(event.check_description, event.check_is_successful, event.check_details, event.time), event
        )

    def on_log_attachment(self, event):
        self._add_step_entry(
            Attachment(event.attachment_description, event.attachment_path, event.as_image, event.time), event
        )

    def on_log_url(self, event):
        self._add_step_entry(
            Url(event.url_description, event.url, event.time), event
        )
