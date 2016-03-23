'''
Created on Mar 19, 2016

@author: nicolas
'''

import sys
import re

from lemoncheesecake.reporting.backend import Backend

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
        init()
    
    def begin_tests(self):
        self.previous_obj = None
    
    def end_tests(self):
        sys.stdout.write("\n")
    
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
        
    def end_testsuite(self):
        pass
    
    def begin_test(self, test):
        self.current_test_line = " -- %2s # %s" % (self.current_test_idx, test.id)
        write_on_line(self.current_test_line + "...")
        self.previous_obj = test
    
    def end_test(self, outcome):
        line = " %s %2s # %s" % (
            colored("OK", "green", attrs=["bold"]) if outcome else colored("OK", "green", attrs=["bold"]),
            self.current_test_idx, self.runtime_state.current_test.id
        )
        raw_line = "%s %2s # %s" % ("OK" if outcome else "KO", self.current_test_idx, self.runtime_state.current_test.id)
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