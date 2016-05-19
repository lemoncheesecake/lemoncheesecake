'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys
import re

from lemoncheesecake.reporting import ReportingBackend
from lemoncheesecake.common import humanize_duration

from colorama import init, Style, Fore
from termcolor import colored

class LinePrinter:
    def __init__(self):
        self.prev_len = 0
    
    def print_line(self, line, force_len=None):
        value_len = force_len if force_len else len(line) 
        if type(line) is unicode:
            line = line.encode("utf-8")
        
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

CTX_BEFORE_SUITE = 0
CTX_TEST = 1
CTX_AFTER_SUITE = 2

class ConsoleBackend(ReportingBackend):
    def __init__(self):
        init() # init colorama
        self.lp = LinePrinter()
    
    def begin_tests(self):
        self.previous_obj = None
 
    def begin_before_suite(self, testsuite):
        self.context = CTX_BEFORE_SUITE
        self.current_test_idx = 1

        if not testsuite.has_selected_tests(deep=False):
            return

        path = testsuite.get_path_str()
        path_len = len(path)
        if self.previous_obj:
            sys.stdout.write("\n")
        sys.stdout.write("=" * 30 + " " + colored(testsuite.get_path_str(), attrs=["bold"]) + " " + "=" * (40 - path_len) + "\n")
        self.previous_obj = testsuite
    
    def end_before_suite(self, testsuite):
        self.lp.erase_line()
        
    def begin_after_suite(self, testsuite):
        self.context = CTX_AFTER_SUITE
    
    def end_after_suite(self, testsuite):
        self.lp.erase_line()
        
    def begin_test(self, test):
        self.context = CTX_TEST
        self.current_test_line = " -- %2s # %s" % (self.current_test_idx, test.id)
        self.lp.print_line(self.current_test_line + "...")
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
        if self.context == CTX_BEFORE_SUITE:
            self.lp.print_line(" => before suite: %s" % description)
        elif self.context == CTX_AFTER_SUITE:
            self.lp.print_line(" => after suite: %s" % description)
        else:
            description += "..."
            line = "%s (%s)" % (self.current_test_line, description)
            line = re.sub("^(.{70})(.+)(.{30})$", "\\1...\\3", line)
            self.lp.print_line(line)
    
    def log(self, content, level):
        pass
    
    def end_tests(self):
        self.reporting_data.refresh_stats()
        print()
        print(colored("Statistics", attrs=["bold"]), ":")
        print(" * Duration: %s" % humanize_duration(self.reporting_data.end_time - self.reporting_data.start_time))
        print(" * Tests: %d" % self.reporting_data.tests)
        print(" * Successes: %d (%d%%)" % (self.reporting_data.tests_success, float(self.reporting_data.tests_success) / self.reporting_data.tests * 100 if self.reporting_data.tests else 0))
        print(" * Failures: %d" % (self.reporting_data.tests_failure))
        print()
        