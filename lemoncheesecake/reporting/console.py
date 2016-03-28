'''
Created on Mar 19, 2016

@author: nicolas
'''

import sys
import re

from lemoncheesecake.reporting.backend import Backend
from lemoncheesecake.common import humanize_duration

from colorama import init, Style, Fore
from termcolor import colored

prev_len = 0
def write_on_line(value, force_len=None):
    global prev_len
    if prev_len:
        sys.stdout.write("\b" * prev_len)

    value_len = force_len if force_len else len(value) 
    if type(value) is unicode:
        value = value.encode("utf-8")
    sys.stdout.write(value)
    if prev_len > value_len:
        sys.stdout.write(" " * (prev_len - value_len))
    prev_len = value_len
    sys.stdout.write("\b" * (prev_len - value_len))
    sys.stdout.flush()

def flush_line():
    global prev_len
    prev_len = 0
    sys.stdout.write("\n")
    sys.stdout.flush()

class ConsoleBackend(Backend):
    def __init__(self):
        init() # init colorama
    
    def begin_tests(self):
        self.previous_obj = None
 
    def begin_testsuite(self, testsuite):
        if not testsuite.get_tests():
            return

        self.current_test_idx = 1
        path = testsuite.get_path_str()
        path_len = len(path)
        if self.previous_obj:
            sys.stdout.write("\n")
        sys.stdout.write("=" * 30 + " " + colored(testsuite.get_path_str(), attrs=["bold"]) + " " + "=" * (40 - path_len) + "\n")
        self.previous_obj = testsuite
        
    def end_testsuite(self, testsuite):
        pass
    
    def begin_test(self, test):
        self.current_test_line = " -- %2s # %s" % (self.current_test_idx, test.id)
        write_on_line(self.current_test_line + "...")
        self.previous_obj = test
    
    def end_test(self, test, outcome):
        line = " %s %2s # %s" % (
            colored("OK", "green", attrs=["bold"]) if outcome else colored("KO", "red", attrs=["bold"]),
            self.current_test_idx, test.id
        )
        raw_line = "%s %2s # %s" % ("OK" if outcome else "KO", self.current_test_idx, test.id)
        write_on_line(line, force_len=len(raw_line))
        flush_line()
        self.current_test_idx += 1
    
    def set_step(self, description):
        description += "..."
        line = "%s (%s)" % (self.current_test_line, description)
        line = re.sub("^(.{70})(.+)(.{30})$", "\\1...\\3", line)
        write_on_line(line)
    
    def log(self, content, level):
        pass
    
    def end_tests(self):
        self.test_results.refresh_stats()
        print
        print colored("Statistics", attrs=["bold"]), ":"
        print " * Duration: %s" % humanize_duration(self.test_results.end_time - self.test_results.start_time)
        print " * Tests: %d" % self.test_results.tests
        print " * Successes: %d (%d%%)" % (self.test_results.tests_success, float(self.test_results.tests_success) / self.test_results.tests * 100 if self.test_results.tests else 0)
        print " * Failures: %d" % (self.test_results.tests_failure)
        print
        