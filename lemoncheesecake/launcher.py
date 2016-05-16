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
from lemoncheesecake.testsuite import Filter, AbortTest, AbortTestSuite, AbortAllTests
from lemoncheesecake import reporting
from lemoncheesecake.reportingbackends.console import ConsoleBackend
from lemoncheesecake.reportingbackends.xml import XmlBackend
from lemoncheesecake.reportingbackends.json_ import JsonBackend
from lemoncheesecake.reportingbackends.html import HtmlBackend

COMMAND_RUN = "run"

class Launcher:
    def __init__(self):
        self.cli_parser = argparse.ArgumentParser()
        subparsers = self.cli_parser.add_subparsers(dest="command")
        self.cli_run_parser = subparsers.add_parser(COMMAND_RUN)
        self.cli_run_parser.add_argument("--test-id", "-t", nargs="+", default=[], help="Filters on test IDs")
        self.cli_run_parser.add_argument("--test-desc", nargs="+", default=[], help="Filters on test descriptions")
        self.cli_run_parser.add_argument("--suite-id", "-s", nargs="+", default=[], help="Filters on test suite IDs")
        self.cli_run_parser.add_argument("--suite-desc", nargs="+", default=[], help="Filters on test suite descriptions")
        self.cli_run_parser.add_argument("--tag", "-a", nargs="+", default=[], help="Filters on test & test suite tags")
        self.cli_run_parser.add_argument("--ticket", "-i", nargs="+", default=[], help="Filters on test & test suite tickets")
        reporting.register_backend("console", ConsoleBackend())
        reporting.register_backend("xml", XmlBackend())
        reporting.register_backend("json", JsonBackend())
        reporting.register_backend("html", HtmlBackend())
    
    def _run_testsuite(self, suite):
        rt = get_runtime()
        
        def handle_exception(e):
            if isinstance(e, AbortTest):
                rt.error(str(e))
            elif isinstance(e, AbortTestSuite):
                rt.error(str(e))
                self.abort_testsuite = suite
            elif isinstance(e, AbortAllTests):
                rt.error(str(e))
                self.abort_all_tests = True
            else:
                # FIXME; use exception instead of last implicit stracktrace
                stacktrace = traceback.format_exc().decode("utf-8")
                rt.error("Caught unexpected exception while running test: " + stacktrace)

        rt.begin_before_suite(suite)
                
        if not self.abort_testsuite and not self.abort_all_tests:
            try:
                suite.before_suite()
            except Exception as e:
                handle_exception(e)
                self.abort_testsuite = suite
            
        rt.end_before_suite() 
        
        for test in suite.get_tests(filtered=True):
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
        
        for sub_suite in suite.get_sub_testsuites(filtered=True):
            self._run_testsuite(sub_suite)

        rt.begin_after_suite(suite)

        try:
            suite.after_suite()
        except Exception as e:
            handle_exception(e)
            
        rt.end_after_suite()
        
        # reset the abort suite flag
        if self.abort_testsuite == suite:
            self.abort_testsuite = None
        
    def run_testsuites(self, project, filter):
        # load project
        project.load_settings()
        project.load_testsuites()
        
        # retrieve test suites
        if filter.is_empty():
            testsuites = project.testsuites
        else:
            testsuites = []
            for suite in project.testsuites:
                suite.apply_filter(filter)
                if suite.has_selected_tests():
                    testsuites.append(suite)
            if not testsuites:
                raise LemonCheesecakeException("The test filter does not match any test.")
                
        # initialize runtime & global test variables
        report_dir  = project.settings.reports_root_dir
        report_dir += os.path.sep
        report_dir += project.settings.report_dir_format(project.settings.reports_root_dir, time.time())
        os.mkdir(report_dir)
        # FIXME: the symlink is not portable
        symlink_path = os.path.join(project.settings.reports_root_dir, "..", "last_report")
        if os.path.exists(symlink_path):
            os.unlink(symlink_path)
        os.symlink(report_dir, symlink_path)
        initialize_runtime(report_dir)
        rt = get_runtime()
        for backend in project.settings.report_backends:
            rt.report_backends.append(reporting.get_backend(backend))
        rt.init_reporting_backends()
        self.abort_all_tests = False
        self.abort_testsuite = None
        
        # init report information
        rt.reporting_data.add_info("Command line", " ".join(sys.argv))
        
        # run tests
        rt.begin_tests()
        for suite in testsuites:
            self._run_testsuite(suite)
        rt.end_tests()

    def cli_run_testsuites(self, args):
        # init filter
        filter = Filter()
        filter.test_id = args.test_id
        filter.test_description = args.test_desc
        filter.testsuite_id = args.suite_id
        filter.testsuite_description = args.suite_desc
        filter.tags = args.tag
        filter.tickets = args.ticket
        
        # init project and run tests
        project = Project(".")
        self.run_testsuites(project, filter)
        
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