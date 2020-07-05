'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys

from termcolor import colored
import six

from lemoncheesecake.testtree import filter_suites, flatten_suites
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession, ReportingSessionBuilderMixin
from lemoncheesecake.reporting.report import ReportStats
from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.helpers.text import ensure_single_line_text
from lemoncheesecake.helpers import terminalsize
from lemoncheesecake.reporting.console import test_status_to_color


class LinePrinter:
    def __init__(self, terminal_width):
        self.terminal_width = terminal_width
        self.prev_len = 0

    def print_line(self, line, force_len=None):
        value_len = force_len if force_len else len(line)
        if six.PY2:
            if type(line) is unicode:
                line = line.encode("utf-8")

        if value_len >= self.terminal_width - 1:
            line = line[:self.terminal_width - 5] + "..."
            value_len = len(line)

        sys.stdout.write("\r")
        sys.stdout.write(line)
        if self.prev_len > value_len:
            sys.stdout.write(" " * (self.prev_len - value_len))
        sys.stdout.flush()

        self.prev_len = value_len

    def new_line(self):
        self.prev_len = 0
        sys.stdout.write("\n")
        sys.stdout.flush()

    def erase_line(self):
        sys.stdout.write("\r")
        sys.stdout.write(" " * self.prev_len)
        sys.stdout.write("\r")
        self.prev_len = 0


def _make_suite_header_line(suite, terminal_width):
    suite_name = suite.path
    max_width = min((terminal_width, 80))
    # -2 corresponds to the two space characters at the left and right of suite path + another character to avoid
    # an extra line after the suite line on Windows terminal having width <= 80
    padding_total = max_width - 3 - len(suite_name) if len(suite_name) <= (max_width - 3) else 0
    padding_left = padding_total // 2
    padding_right = padding_total // 2 + padding_total % 2

    return "=" * padding_left + " " + colored(suite_name, attrs=["bold"]) + " " + "=" * padding_right


def _make_test_status_label(status):
    if status == "passed":
        label = "OK"
    elif status in ("skipped", "disabled", None):
        label = "--"
    else:
        label = "KO"

    return colored(label, test_status_to_color(status), attrs=["bold"])


def _make_test_result_line(name, num, status):
    line = " %s %2s # %s" % (_make_test_status_label(status), num, name)
    raw_line = "%s %2s # %s" % ("OK" if status == "passed" else "KO", num, name)

    return line, len(raw_line)


def _print_summary(stats, parallel=False):
    print()
    print(colored("Statistics", attrs=["bold"]), ":")
    print(" * Duration: %s" % (humanize_duration(stats.duration) if stats.duration is not None else "n/a"))
    if parallel:
        print(" * Cumulative duration: %s" % stats.duration_cumulative_description)
    print(" * Tests: %d" % stats.tests_nb)
    print(" * Successes: %d (%d%%)" % (stats.tests_nb_by_status["passed"], stats.successful_tests_percentage))
    print(" * Failures: %d" % (stats.tests_nb_by_status["failed"]))
    if stats.tests_nb_by_status["skipped"]:
        print(" * Skipped: %d" % (stats.tests_nb_by_status["skipped"]))
    if stats.tests_nb_by_status["disabled"]:
        print(" * Disabled: %d" % (stats.tests_nb_by_status["disabled"]))
    print()


class SequentialConsoleReportingSession(ReportingSession):
    def __init__(self, terminal_width, show_test_full_path, report):
        self.terminal_width = terminal_width
        self.show_test_full_path = show_test_full_path
        self.report = report
        self.lp = LinePrinter(self.terminal_width)
        self.context = None
        self.custom_step_prefix = None
        self.current_suite = None

    def get_test_label(self, test):
        if self.show_test_full_path:
            return test.path
        return test.name

    def ensure_suite_header_is_displayed(self, suite):
        if suite == self.current_suite:
            return

        self.current_suite = suite
        self.current_test_idx = 1

        if self.previous_obj:
            sys.stdout.write("\n")

        sys.stdout.write(_make_suite_header_line(suite, self.terminal_width) + "\n")

        self.previous_obj = suite

    def on_test_session_start(self, event):
        self.previous_obj = None

    def on_suite_setup_start(self, event):
        self.ensure_suite_header_is_displayed(event.suite)

        self.step_prefix = " => setup suite: "
        self.lp.print_line(self.step_prefix + "...")

    def on_suite_teardown_start(self, event):
        self.step_prefix = " => teardown suite: "
        self.lp.print_line(self.step_prefix + "...")

    def on_test_session_setup_start(self, event):
        self.step_prefix = " => setup test session: "
        self.lp.print_line(self.step_prefix + "...")

    def on_test_session_teardown_start(self, event):
        self.step_prefix = " => teardown test session: "
        self.lp.print_line(self.step_prefix + "...")

    def on_suite_setup_end(self, event):
        self.lp.erase_line()
        self.custom_step_prefix = None

    on_suite_teardown_end = on_suite_setup_end

    def on_test_session_setup_end(self, event):
        self.lp.erase_line()
        self.custom_step_prefix = None

    on_test_session_teardown_end = on_test_session_setup_end

    def on_test_start(self, event):
        self.ensure_suite_header_is_displayed(event.test.parent_suite)

        self.step_prefix = " -- %2s # %s" % (self.current_test_idx, self.get_test_label(event.test))
        self.lp.print_line(self.step_prefix + "...")
        self.previous_obj = event.test

    def on_test_end(self, event):
        test_data = self.report.get_test(event.test)

        line, raw_line_len = _make_test_result_line(
            self.get_test_label(event.test), self.current_test_idx, test_data.status
        )

        self.lp.print_line(line, force_len=raw_line_len)
        self.lp.new_line()

        self.current_test_idx += 1

    def _bypass_test(self, test, status):
        self.ensure_suite_header_is_displayed(test.parent_suite)

        line = " %s %2s # %s" % (_make_test_status_label(status), self.current_test_idx, self.get_test_label(test))
        raw_line = "%s %2s # %s" % ("KO", self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1

    def on_test_skipped(self, event):
        self._bypass_test(event.test, "skipped")

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled")

    def on_step_start(self, event):
        self.lp.print_line("%s (%s...)" % (self.step_prefix, ensure_single_line_text(event.step_description)))

    def on_test_session_end(self, event):
        _print_summary(ReportStats.from_report(self.report), self.report.parallelized)


class ParallelConsoleReportingSession(ReportingSession):
    def __init__(self, terminal_width, report):
        self.terminal_width = terminal_width
        self.report = report
        self.lp = LinePrinter(self.terminal_width)
        self.current_test_idx = 1

    def on_test_end(self, event):
        test_data = self.report.get_test(event.test)

        line, _ = _make_test_result_line(
            event.test.path, self.current_test_idx, test_data.status
        )

        print(line)

        self.current_test_idx += 1

    def _bypass_test(self, test, status):
        line = " %s %2s # %s" % (_make_test_status_label(status), self.current_test_idx, test.path)
        print(line)
        self.current_test_idx += 1

    def on_test_skipped(self, event):
        self._bypass_test(event.test, "skipped")

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled")

    def on_test_session_end(self, event):
        _print_summary(ReportStats.from_report(self.report), self.report.parallelized)


class ConsoleBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width
        self.show_test_full_path = True

    def get_name(self):
        return "console"

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        return \
            ParallelConsoleReportingSession(self.terminal_width, report) if parallel else \
            SequentialConsoleReportingSession(self.terminal_width, self.show_test_full_path, report)


def print_report_as_test_run(report, test_filter):
    suites = filter_suites(report.get_suites(), test_filter)

    ###
    # Setup terminal
    ###
    terminal_width, _ = terminalsize.get_terminal_size()

    ###
    # Display suite results
    ###
    suite_idx = 0
    for suite in flatten_suites(suites):
        if len(suite.get_tests()) == 0:
            continue
        if suite_idx > 0:
            print()
        header_line = _make_suite_header_line(suite, terminal_width)
        print(header_line)
        for test_idx, test in enumerate(suite.get_tests()):
            test_result_line, _ = _make_test_result_line(test.path, num=test_idx+1, status=test.status)
            print(test_result_line)
        suite_idx += 1

    ###
    # Display summary
    ###
    if suite_idx > 0:
        if test_filter:
            stats = ReportStats.from_suites(suites, report.parallelized)
        else:
            stats = ReportStats.from_report(report)
        _print_summary(stats, report.parallelized)
    else:
        print("No test found or no matching test in the report")
