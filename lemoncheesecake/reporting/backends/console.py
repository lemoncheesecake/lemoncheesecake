'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys

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
            return test.get_path_str()
        return test.name

    def begin_tests(self):
        self.previous_obj = None

    def begin_suite(self, testsuite):
        self.current_suite = testsuite
        self.current_test_idx = 1

        if not testsuite.has_selected_tests(deep=False):
            return

        if self.previous_obj:
            sys.stdout.write("\n")

        label = testsuite.get_path_str()
        label_len = len(label)
        max_width = min((self.terminal_width, 80))
        # -2 corresponds to the two space characters at the left and right of testsuite path + another character to avoid
        # an extra line after the testsuite line on Windows terminal having width <= 80
        padding_total = max_width - 3 - label_len if label_len <= (max_width - 3) else 0
        padding_left = padding_total // 2
        padding_right = padding_total // 2 + padding_total % 2
        sys.stdout.write("=" * padding_left + " " + colored(label, attrs=["bold"]) + " " + "=" * padding_right + "\n")
        self.previous_obj = testsuite

    def begin_suite_setup(self, testsuite):
        self.step_prefix = " => setup suite: "
        self.lp.print_line(self.step_prefix + "...")

    def begin_suite_teardown(self, testsuite):
        self.step_prefix = " => teardown suite: "
        self.lp.print_line(self.step_prefix + "...")

    def begin_test_session_setup(self):
        self.step_prefix = " => setup test session: "
        self.lp.print_line(self.step_prefix + "...")

    def begin_test_session_teardown(self):
        self.step_prefix = " => teardown test session: "
        self.lp.print_line(self.step_prefix + "...")

    def end_suite_setup(self, testsuite):
        self.lp.erase_line()
        self.custom_step_prefix = None

    end_suite_teardown = end_suite_setup

    def end_test_session_setup(self):
        self.lp.erase_line()
        self.custom_step_prefix = None

    end_test_session_teardown = end_test_session_setup

    def begin_test(self, test):
        self.step_prefix = " -- %2s # %s" % (self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(self.step_prefix + "...")
        self.previous_obj = test

    def end_test(self, test, status):
        line = " %s %2s # %s" % (
            colored("OK", "green", attrs=["bold"]) if status == "passed" else colored("KO", "red", attrs=["bold"]),
            self.current_test_idx, self.get_test_label(test)
        )
        raw_line = "%s %2s # %s" % ("OK" if status == "passed" else "KO", self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1

    def bypass_test(self, test, status, status_details):
        line = " %s %2s # %s" % (
            colored("KO", "yellow", attrs=["bold"]),
            self.current_test_idx, self.get_test_label(test)
        )
        raw_line = "%s %2s # %s" % ("KO", self.current_test_idx, self.get_test_label(test))
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1

    def set_step(self, description):
        self.lp.print_line("%s (%s...)" % (self.step_prefix, description))

    def log(self, content, level):
        pass

    def end_tests(self):
        report = self.report
        stats = report.get_stats()

        print()
        print(colored("Statistics", attrs=["bold"]), ":")
        print(" * Duration: %s" % humanize_duration(report.end_time - report.start_time))
        print(" * Tests: %d" % stats.tests)
        print(" * Successes: %d (%d%%)" % (
            stats.test_statuses["passed"], float(stats.test_statuses["passed"]) / stats.tests * 100 if stats.tests else 0)
        )
        print(" * Failures: %d" % (stats.test_statuses["failed"]))
        if stats.test_statuses["skipped"]:
            print(" * Skipped: %d" % (stats.test_statuses["skipped"]))
        print()

class ConsoleBackend(ReportingBackend):
    name = "console"

    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width
        self.show_test_full_path = False

    def create_reporting_session(self, report_dir, report):
        return ConsoleReportingSession(self.terminal_width, self.show_test_full_path, report)
