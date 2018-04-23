'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.reporting.report import *
from lemoncheesecake import events
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "ReportWriter", "initialize_report_writer"


class ReportWriter:
    def __init__(self, report):
        self.report = report

    def _get_test_data(self, test):
        return self.report.get_test(test)

    def _get_suite_data(self, suite):
        return self.report.get_suite(suite)

    def _add_step_entry(self, entry, event):
        report_node_data = self.report.get(event.location)
        step = self._lookup_step(report_node_data.steps, event.step)
        if step.end_time:
            raise ProgrammingError("Cannot update step '%s', it is already ended" % step.description)
        step.entries.append(entry)

    @staticmethod
    def _start_hook(ts):
        hook_data = HookData()
        hook_data.start_time = ts
        return hook_data

    @staticmethod
    def _end_hook(hook_data, ts):
        if hook_data:
            hook_data.end_time = ts
            hook_data.outcome = not hook_data.has_failure()

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

    @staticmethod
    def _finalize_steps(steps, end_time):
        if not steps:
            return
        for step in steps[:]:
            if step.entries:
                # set step end time (last step or detached step)
                if not step.end_time:
                    step.end_time = end_time
            else:
                # remove empty step
                steps.remove(step)

    def on_test_session_start(self, event):
        self.report.start_time = event.time

    def on_test_session_end(self, event):
        self.report.end_time = event.time
        self.report.report_generation_time = self.report.end_time

    def on_test_session_setup_start(self, event):
        self.report.test_session_setup = self._start_hook(event.time)

    def on_test_session_setup_end(self, event):
        self._finalize_steps(self.report.test_session_setup.steps, event.time)

        if self.report.test_session_setup.is_empty():
            self.report.test_session_setup = None
        else:
            self._end_hook(self.report.test_session_setup, event.time)

    def on_test_session_teardown_start(self, event):
        self.report.test_session_teardown = self._start_hook(event.time)

    def on_test_session_teardown_end(self, event):
        self._finalize_steps(self.report.test_session_teardown.steps, event.time)

        if self.report.test_session_teardown.is_empty():
            self.report.test_session_teardown = None
        else:
            self._end_hook(self.report.test_session_teardown, event.time)

    def on_suite_start(self, event):
        suite = event.suite
        suite_data = SuiteData(suite.name, suite.description)
        suite_data.tags.extend(suite.tags)
        suite_data.properties.update(suite.properties)
        suite_data.links.extend(suite.links)
        suite_data.rank = suite.rank
        if suite.parent_suite:
            parent_suite_data = self._get_suite_data(suite.parent_suite)
            parent_suite_data.add_suite(suite_data)
        else:
            self.report.add_suite(suite_data)

    def on_suite_setup_start(self, event):
        suite_data = self._get_suite_data(event.suite)
        suite_data.suite_setup = self._start_hook(event.time)

    def on_suite_setup_end(self, event):
        suite_data = self._get_suite_data(event.suite)
        self._finalize_steps(suite_data.suite_setup.steps, event.time)

        if suite_data.suite_setup.is_empty():
            suite_data.suite_setup = None
        else:
            self._end_hook(suite_data.suite_setup, event.time)

    def on_suite_teardown_start(self, event):
        suite_data = self._get_suite_data(event.suite)

        suite_data.suite_teardown = self._start_hook(event.time)

    def on_suite_teardown_end(self, event):
        suite_data = self._get_suite_data(event.suite)
        self._finalize_steps(suite_data.suite_teardown.steps, event.time)

        if suite_data.suite_teardown.is_empty():
            suite_data.suite_teardown = None
        else:
            self._end_hook(suite_data.suite_teardown, event.time)

    def on_test_start(self, event):
        test = event.test

        test_data = TestData(test.name, test.description)
        test_data.tags.extend(test.tags)
        test_data.properties.update(test.properties)
        test_data.links.extend(test.links)
        test_data.rank = test.rank
        test_data.start_time = event.time

        suite_data = self._get_suite_data(event.test.parent_suite)
        suite_data.add_test(test_data)

    def on_test_end(self, event):
        test_data = self._get_test_data(event.test)
        self._finalize_steps(test_data.steps, event.time)

        test_data.status = "failed" if test_data.has_failure() else "passed"
        test_data.end_time = event.time

    def _bypass_test(self, test, status, status_details, time):
        test_data = TestData(test.name, test.description)
        test_data.tags.extend(test.tags)
        test_data.properties.update(test.properties)
        test_data.links.extend(test.links)
        test_data.end_time = test_data.start_time = time
        test_data.status = status
        test_data.status_details = status_details

        suite_data = self._get_suite_data(test.parent_suite)
        suite_data.add_test(test_data)

    def on_test_skipped(self, event):
        self._bypass_test(event.test, "skipped", event.skipped_reason, event.time)

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled", "", event.time)

    def on_step(self, event):
        report_node_data = self.report.get(event.location)
        current_step = self._lookup_current_step(report_node_data.steps)
        if current_step:
            current_step.end_time = event.time

        new_step = StepData(event.step_description, detached=event.detached)
        new_step.start_time = event.time
        report_node_data.steps.append(new_step)

    def on_step_end(self, event):
        report_node_data = self.report.get(event.location)
        step = self._lookup_step(report_node_data.steps, event.step)

        # only detached steps can be explicitly ended, otherwise do nothing
        if step._detached:
            step.end_time = event.time

    def on_log(self, event):
        self._add_step_entry(
            LogData(event.log_level, event.log_message, event.time), event
        )

    def on_check(self, event):
        self._add_step_entry(
            CheckData(event.check_description, event.check_outcome, event.check_details), event
        )

    def on_log_attachment(self, event):
        self._add_step_entry(
            AttachmentData(event.attachment_description, event.attachment_path), event
        )

    def on_log_url(self, event):
        self._add_step_entry(
            UrlData(event.url_description, event.url), event
        )


def initialize_report_writer(report):
    writer = ReportWriter(report)
    events.add_listener(writer)
    return writer
