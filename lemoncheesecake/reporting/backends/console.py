'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys

import colorama
from termcolor import colored

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.reporting.backends import terminalsize
from lemoncheesecake.reporting.report import get_stats_from_suites
from lemoncheesecake.filter import filter_suites
from lemoncheesecake.testtree import flatten_suites
from lemoncheesecake.utils import IS_PYTHON3, humanize_duration, get_status_color


class LinePrinter:
    def __init__(self, terminal_width):
        self.terminal_width = terminal_width
        self.prev_len = 0

    def print_line(self, line, force_len=None):
        value_len = force_len if force_len else len(line)
        if not IS_PYTHON3:
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
    elif status == "disabled":
        label = "--"
    else:
        label = "KO"

    return colored(label, get_status_color(status), attrs=["bold"])


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
    print(" * Tests: %d" % stats.tests)
    print(" * Successes: %d (%d%%)" % (stats.test_statuses["passed"], stats.successful_tests_percentage))
    print(" * Failures: %d" % (stats.test_statuses["failed"]))
    if stats.test_statuses["skipped"]:
        print(" * Skipped: %d" % (stats.test_statuses["skipped"]))
    if stats.test_statuses["disabled"]:
        print(" * Disabled: %d" % (stats.test_statuses["disabled"]))
    print()


class SequentialConsoleReportingSession(ReportingSession):
    def __init__(self, terminal_width, show_test_full_path, report):
        self.terminal_width = terminal_width
        self.show_test_full_path = show_test_full_path
        self.report = report
        colorama.init()
        self.lp = LinePrinter(self.terminal_width)
        self.context = None
        self.custom_step_prefix = None
        self.current_suite = None

    def get_test_label(self, test):
        if self.show_test_full_path:
            return test.path
        return test.name

    def on_test_session_start(self, event):
        self.previous_obj = None

    def on_suite_start(self, event):
        suite = event.suite
        self.current_suite = suite
        self.current_test_idx = 1

        if not suite.get_tests():
            return

        if self.previous_obj:
            sys.stdout.write("\n")

        sys.stdout.write(_make_suite_header_line(suite, self.terminal_width) + "\n")

        self.previous_obj = suite

    def on_suite_setup_start(self, event):
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
        line = " %s %2s # %s" % (_make_test_status_label(status), self.current_test_idx, self.get_test_label(test))
        raw_line = "%s %2s # %s" % ("KO", self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1

    def on_test_skipped(self, event):
        self._bypass_test(event.test, "skipped")

    def on_test_disabled(self, event):
        self._bypass_test(event.test, "disabled")

    def on_step(self, event):
        self.lp.print_line("%s (%s...)" % (self.step_prefix, event.step_description))

    def on_test_session_end(self, event):
        _print_summary(self.report.stats(), self.report.parallelized)


class ParallelConsoleReportingSession(ReportingSession):
    def __init__(self, terminal_width, report):
        self.terminal_width = terminal_width
        self.report = report
        colorama.init()
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
        _print_summary(self.report.stats(), self.report.parallelized)


class ConsoleBackend(ReportingBackend):
    name = "console"

    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width
        self.show_test_full_path = False

    def create_reporting_session(self, report_dir, report, parallel=False):
        return \
            ParallelConsoleReportingSession(self.terminal_width, report) if parallel else \
            SequentialConsoleReportingSession(self.terminal_width, self.show_test_full_path, report)


def display_report(report, filtr):
    suites = filter_suites(report.get_suites(), filtr)

    ###
    # Setup terminal
    ###
    colorama.init()
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
        if filtr.is_empty():
            stats = report.stats()
        else:
            stats = get_stats_from_suites(suites, report.parallelized)
        _print_summary(stats, report.parallelized)
    else:
        print("No test found in report")
