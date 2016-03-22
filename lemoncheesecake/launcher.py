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
from lemoncheesecake.reporting.console import ConsoleBackend 

COMMAND_RUN = "run"

class Launcher:
    def __init__(self):
        self.cli_parser = argparse.ArgumentParser()
        subparsers = self.cli_parser.add_subparsers(dest="command")
        self.cli_run_parser = subparsers.add_parser(COMMAND_RUN)
    
    def _run_testsuite(self, suite):
        rt = get_runtime()
        
        rt.begin_testsuite(suite)
        suite.before_suite()
        
        for test in suite.get_tests():
            rt.begin_test(test)
            suite.before_test(test.id)
            test.callback(suite)
            suite.after_test(test.id)
            rt.end_test()
        
        for sub_suite in suite.get_sub_testsuites():
            self._run_testsuite(sub_suite)

        suite.after_suite()
        rt.end_testsuite()
        
    def run_testsuites(self, project):
        # load project
        project.load_settings()
        project.load_testsuites()
        
        # initialize runtime
        initialize_runtime("report-%d" % time.time())
        rt = get_runtime()
        rt.reporting_backends.append(ConsoleBackend())
        rt.init_reporting_backends()
        
        # run tests
        rt.begin_tests()
        for suite in project.testsuites:
            self._run_testsuite(suite)
        rt.end_tests()

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