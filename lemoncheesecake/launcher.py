'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import os, os.path
import time
import argparse

import traceback

from lemoncheesecake.project import Project
from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.common import LemonCheesecakeException
from lemoncheesecake import reporting
from lemoncheesecake.reportbackends.console import ConsoleBackend
from lemoncheesecake.reportbackends.xml import XmlBackend
from lemoncheesecake.testsuite import AbortTest, AbortTestSuite, AbortAllTests

COMMAND_RUN = "run"

class Launcher:
    def __init__(self):
        self.cli_parser = argparse.ArgumentParser()
        subparsers = self.cli_parser.add_subparsers(dest="command")
        self.cli_run_parser = subparsers.add_parser(COMMAND_RUN)
        reporting.register_backend("console", ConsoleBackend())
        reporting.register_backend("xml", XmlBackend())
    
    def _run_testsuite(self, suite):
        rt = get_runtime()
        
        def handle_exception(e):
            if isinstance(e, AbortTest):
                rt.error("The test has been aborted")
            elif isinstance(e, AbortTestSuite):
                rt.error("The test suite has been aborted")
                self.abort_testsuite = suite
            elif isinstance(e, AbortAllTests):
                rt.error("All tests have been aborted")
                self.abort_all_tests = True
            else:
                # FIXME; use exception instead of last implicit stracktrace
                stacktrace = traceback.format_exc().decode("utf-8")
                rt.error("Caught exception while running test: " + stacktrace)
            
        try:
            rt.begin_testsuite(suite)
        except Exception as e:
            handle_exception(e)
            self.abort_testsuite = suite 
        
        if not self.abort_testsuite and not self.abort_all_tests:
            suite.before_suite()
        
        for test in suite.get_tests():
            rt.begin_test(test)
            if self.abort_testsuite:
                rt.error("Cannot execute this test: the tests of this test suite have been aborted.")
                rt.end_test()
                continue
            if self.abort_all_tests:
                rt.error("Cannot execute this test: all tests have been aborted.")
                rt.end_test()
                continue

            try:
                suite.before_test(test.id)
                test.callback(suite)
            except Exception as e:
                handle_exception(e)
                rt.end_test()
                continue
            
            try:
                suite.after_test(test.id)
            except Exception as e:
                handle_exception(e)
                rt.end_test()
                continue
            
            rt.end_test()
        
        for sub_suite in suite.get_sub_testsuites():
            self._run_testsuite(sub_suite)

        try:
            suite.after_suite()
        except Exception as e:
            handle_exception(e)
            
        rt.end_testsuite()
        
        # reset the abort suite flag
        if self.abort_testsuite == suite:
            self.abort_testsuite = None
        
    def run_testsuites(self, project):
        # load project
        project.load_settings()
        project.load_testsuites()
        
        # initialize runtime & global test variables
        report_dir  = project.settings.reports_root_dir
        report_dir += os.path.sep
        report_dir += project.settings.report_dir_format(project.settings.reports_root_dir, time.time())
        os.mkdir(report_dir)
        initialize_runtime(report_dir)
        rt = get_runtime()
        for backend in project.settings.report_backends:
            rt.report_backends.append(reporting.get_backend(backend))
        rt.init_reporting_backends()
        self.abort_all_tests = False
        self.abort_testsuite = None
        
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