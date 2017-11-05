'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys

from lemoncheesecake.testtree import get_flattened_suites
from lemoncheesecake.reporting.report import get_stats_from_suites
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.utils import IS_PYTHON3, humanize_duration
from lemoncheesecake.reporting.backends import terminalsize

import colorama
from termcolor import colored


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
    suite_name = suite.get_path_as_str()
    max_width = min((terminal_width, 80))
    # -2 corresponds to the two space characters at the left and right of suite path + another character to avoid
    # an extra line after the suite line on Windows terminal having width <= 80
    padding_total = max_width - 3 - len(suite_name) if len(suite_name) <= (max_width - 3) else 0
    padding_left = padding_total // 2
    padding_right = padding_total // 2 + padding_total % 2

    return "=" * padding_left + " " + colored(suite_name, attrs=["bold"]) + " " + "=" * padding_right


def _make_test_result_line(name, num, status):
    line = " %s %2s # %s" % (
        colored("OK", "green", attrs=["bold"]) if status == "passed" else colored("KO", "red", attrs=["bold"]),
        num, name
    )
    raw_line = "%s %2s # %s" % ("OK" if status == "passed" else "KO", num, name)

    return line, len(raw_line)


def _print_summary(stats, duration):
    print()
    print(colored("Statistics", attrs=["bold"]), ":")
    print(" * Duration: %s" % humanize_duration(duration))
    print(" * Tests: %d" % stats.tests)
    print(" * Successes: %d (%d%%)" % (
        stats.test_statuses["passed"], float(stats.test_statuses["passed"]) / stats.tests * 100 if stats.tests else 0)
          )
    print(" * Failures: %d" % (stats.test_statuses["failed"]))
    if stats.test_statuses["skipped"]:
        print(" * Skipped: %d" % (stats.test_statuses["skipped"]))
    print()


class ConsoleReportingSession(ReportingSession):
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
            return test.get_path_as_str()
        return test.name

    def on_tests_beginning(self, report):
        self.previous_obj = None

    def on_suite_beginning(self, suite):
        self.current_suite = suite
        self.current_test_idx = 1

        if not suite.get_tests():
            return

        if self.previous_obj:
            sys.stdout.write("\n")

        sys.stdout.write(_make_suite_header_line(suite, self.terminal_width) + "\n")

        self.previous_obj = suite

    def on_suite_setup_beginning(self, suite):
        self.step_prefix = " => setup suite: "
        self.lp.print_line(self.step_prefix + "...")

    def on_suite_teardown_beginning(self, suite):
        self.step_prefix = " => teardown suite: "
        self.lp.print_line(self.step_prefix + "...")

    def on_test_session_setup_beginning(self):
        self.step_prefix = " => setup test session: "
        self.lp.print_line(self.step_prefix + "...")

    def on_test_session_teardown_beginning(self):
        self.step_prefix = " => teardown test session: "
        self.lp.print_line(self.step_prefix + "...")

    def on_suite_setup_ending(self, suite, outcome):
        self.lp.erase_line()
        self.custom_step_prefix = None

    on_suite_teardown_ending = on_suite_setup_ending

    def on_test_session_setup_ending(self, outcome):
        self.lp.erase_line()
        self.custom_step_prefix = None

    on_test_session_teardown_ending = on_test_session_setup_ending

    def on_test_beginning(self, test):
        self.step_prefix = " -- %2s # %s" % (self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(self.step_prefix + "...")
        self.previous_obj = test

    def on_test_ending(self, test, status):
        line, raw_line_len = _make_test_result_line(self.get_test_label(test), self.current_test_idx, status)

        self.lp.print_line(line, force_len=raw_line_len)
        self.lp.new_line()

        self.current_test_idx += 1

    def _bypass_test(self, test):
        line = " %s %2s # %s" % (
            colored("KO", "yellow", attrs=["bold"]),
            self.current_test_idx, self.get_test_label(test)
        )
        raw_line = "%s %2s # %s" % ("KO", self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1

    def on_skipped_test(self, test, reason):
        self._bypass_test(test)

    def on_disabled_test(self, test):
        self._bypass_test(test)

    def on_step(self, description):
        self.lp.print_line("%s (%s...)" % (self.step_prefix, description))

    def on_log(self, content, level):
        pass

    def on_tests_ending(self, report):
        _print_summary(self.report.get_stats(), duration=self.report.end_time - self.report.start_time)


class ConsoleBackend(ReportingBackend):
    name = "console"

    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width
        self.show_test_full_path = False

    def create_reporting_session(self, report_dir, report):
        return ConsoleReportingSession(self.terminal_width, self.show_test_full_path, report)


def display_report_suites(suites):
    ###
    # Setup terminal
    ###
    colorama.init()
    terminal_width, _ = terminalsize.get_terminal_size()

    ###
    # Display suite results
    ###
    suite_idx = 0
    for suite in get_flattened_suites(suites):
        if len(suite.get_tests()) == 0:
            continue
        if suite_idx > 0:
            print()
        header_line = _make_suite_header_line(suite, terminal_width)
        print(header_line)
        for test_idx, test in enumerate(suite.get_tests()):
            test_result_line, _ = _make_test_result_line(test.get_path_as_str(), num=test_idx+1, status=test.status)
            print(test_result_line)
        suite_idx += 1

    ###
    # Display summary
    ###
    if suite_idx > 0:
        stats = get_stats_from_suites(suites)
        _print_summary(stats, stats.duration)
    else:
        print("No test found in report")
