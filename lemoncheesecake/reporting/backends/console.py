'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys
import re

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.utils import IS_PYTHON3, humanize_duration
from lemoncheesecake.reporting.backends import terminalsize

from colorama import init, Style, Fore
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
    def __init__(self, report, report_dir, terminal_width, display_testsuite_full_path):
        ReportingSession.__init__(self, report, report_dir)
        init() # init colorama
        self.lp = LinePrinter(terminal_width)
        self.terminal_width = terminal_width
        self.display_testsuite_full_path = display_testsuite_full_path
        self.context = None
        self.custom_step_prefix = None
    
    def begin_tests(self):
        self.previous_obj = None
 
    def begin_suite(self, testsuite):
        self.current_test_idx = 1

        if not testsuite.has_selected_tests(deep=False):
            return

        if self.previous_obj:
            sys.stdout.write("\n")

        label = testsuite.get_path_str() if self.display_testsuite_full_path else testsuite.id
        label_len = len(label)
        max_width = min((self.terminal_width, 80))
        # -2 corresponds to the two space characters at the left and right of testsuite path + another character to avoid
        # an extra line after the testsuite line on Windows terminal having width <= 80
        padding_total = max_width - 3 - label_len if label_len <= (max_width - 3) else 0
        padding_left = padding_total // 2
        padding_right = padding_total // 2 + padding_total % 2
        sys.stdout.write("=" * padding_left + " " + colored(label, attrs=["bold"]) + " " + "=" * padding_right + "\n")
        self.previous_obj = testsuite
    
    def begin_before_suite(self, testsuite):
        self.step_prefix = " => before suite: "
        self.lp.print_line(self.step_prefix + "...")
    
    def begin_after_suite(self, testsuite):
        self.step_prefix = " => after suite: "
        self.lp.print_line(self.step_prefix + "...")
    
    def begin_worker_before_all_tests(self):
        self.step_prefix = " => before all tests: "
        self.lp.print_line(self.step_prefix + "...")
    
    def begin_worker_after_all_tests(self):
        self.step_prefix = " => after all tests: "
        self.lp.print_line(self.step_prefix + "...")
    
    def end_before_suite(self, testsuite):
        self.lp.erase_line()
        self.custom_step_prefix = None
    
    end_after_suite = end_before_suite
    
    def end_worker_before_all_tests(self):
        self.lp.erase_line()
        self.custom_step_prefix = None
    
    end_worker_after_all_tests = end_worker_before_all_tests
            
    def begin_test(self, test):
        self.step_prefix = " -- %2s # %s" % (self.current_test_idx, test.id)
        self.lp.print_line(self.step_prefix + "...")
        self.previous_obj = test
    
    def end_test(self, test, outcome):
        line = " %s %2s # %s" % (
            colored("OK", "green", attrs=["bold"]) if outcome else colored("KO", "red", attrs=["bold"]),
            self.current_test_idx, test.id
        )
        raw_line = "%s %2s # %s" % ("OK" if outcome else "KO", self.current_test_idx, test.id)
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
        print(" * Successes: %d (%d%%)" % (stats.test_successes, float(stats.test_successes) / stats.tests * 100 if stats.tests else 0))
        print(" * Failures: %d" % (stats.test_failures))
        print()

class ConsoleBackend(ReportingBackend):
    name = "console"
    
    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width
        self.display_testsuite_full_path = True

    def create_reporting_session(self, report, report_dir):
        return ConsoleReportingSession(report, report_dir, self.terminal_width, self.display_testsuite_full_path)
