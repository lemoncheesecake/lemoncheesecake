'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import time
import argparse

from lemoncheesecake.project import Project
from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.common import LemonCheesecakeException

COMMAND_RUN = "run"

class Launcher:
    def __init__(self):
        self.cli_parser = argparse.ArgumentParser()
        subparsers = self.cli_parser.add_subparsers(dest="command")
        self.cli_run_parser = subparsers.add_parser(COMMAND_RUN)
    
    def _run_testsuite(self, suite):
        suite.before_suite()
        
        for test in suite.get_tests():
            suite.before_test(test.id)
            test.callback(suite)
            suite.after_test(test.id)
        
        for sub_suite in suite.get_sub_testsuites():
            self._run_testsuite(sub_suite)

        suite.after_suite()
        
    def run_testsuites(self, project):
        project.load_settings()
        project.load_testsuites()
        initialize_runtime("report-%d" % time.time())
        for suite in project.testsuites:
            self._run_testsuite(suite)
    
    def cli_run_testsuites(self, args):
        project = Project(".")
        self.run_testsuites(project)
        
    def handle_cli(self):
        try:
            args = self.cli_parser.parse_args()
            if args.command == COMMAND_RUN:
                self.cli_run_testsuites(args)
        except LemonCheesecakeException as e:
            sys.exit(e)
        
        sys.exit(0)
        

if __name__ == "__main__":
    launcher = Launcher()
    launcher.handle_cli()