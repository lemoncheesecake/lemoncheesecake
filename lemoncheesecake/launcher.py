'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import os, os.path
import re
import importlib
import glob
import platform
import time
import argparse
import traceback

from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.common import LemonCheesecakeException, IS_PYTHON3
from lemoncheesecake.testsuite import Filter, AbortTest, AbortTestSuite, AbortAllTests
import lemoncheesecake.worker
from lemoncheesecake import reporting
from lemoncheesecake.reportingbackends.console import ConsoleBackend
from lemoncheesecake.reportingbackends.xml import XmlBackend
from lemoncheesecake.reportingbackends.json_ import JsonBackend
from lemoncheesecake.reportingbackends.html import HtmlBackend

COMMAND_RUN = "run"

class CannotLoadTestSuite(LemonCheesecakeException):
    pass

def reporting_dir_with_datetime(report_rootdir, t):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(t))

def _strip_py_ext(filename):
    return re.sub("\.py$", "", filename)

def get_testsuite_from_file(filename):
    mod_path = _strip_py_ext(filename.replace(os.path.sep, "."))
    mod_name = mod_path.split(".")[-1]

    loaded_mod = importlib.import_module(mod_path)
    try:
        klass = getattr(loaded_mod, mod_name)
    except AttributeError:
        raise Exception("Cannot find class '%s' in '%s'" % (mod_name, loaded_mod.__file__))
    return klass

def get_testsuites_from_directory(dir, recursive=True):
    suites = [ ]
    for filename in glob.glob(os.path.join(dir, "*.py")):
        if os.path.basename(filename).startswith("__"):
            continue
        suite = get_testsuite_from_file(filename)
        if recursive:
            suite_subdir = _strip_py_ext(filename) + "_suites"
            if os.path.isdir(suite_subdir):
                sub_suites = get_testsuites_from_directory(suite_subdir, recursive=True)
                for sub_suite in sub_suites:
                    setattr(suite, sub_suite.__name__, sub_suite)
        suites.append(suite)
    if len(list(filter(lambda s: hasattr(s, "_rank"), suites))) == len(suites):
        suites.sort(key=lambda s: s._rank)
    return suites

class Launcher:
    def __init__(self):
        self.cli_parser = argparse.ArgumentParser()

        ###
        # CLI setup
        ###
        subparsers = self.cli_parser.add_subparsers(dest="command")
        self.cli_run_parser = subparsers.add_parser(COMMAND_RUN)
        self.cli_run_parser.add_argument("--test-id", "-t", nargs="+", default=[], help="Filters on test IDs")
        self.cli_run_parser.add_argument("--test-desc", nargs="+", default=[], help="Filters on test descriptions")
        self.cli_run_parser.add_argument("--suite-id", "-s", nargs="+", default=[], help="Filters on test suite IDs")
        self.cli_run_parser.add_argument("--suite-desc", nargs="+", default=[], help="Filters on test suite descriptions")
        self.cli_run_parser.add_argument("--tag", "-a", nargs="+", default=[], help="Filters on test & test suite tags")
        self.cli_run_parser.add_argument("--ticket", "-i", nargs="+", default=[], help="Filters on test & test suite tickets")
        self.cli_run_parser.add_argument("--report-dir", "-r", required=False, help="Directory where reporting data will be stored")
        
        ###
        # Default reporting setup when no --report-dir has been setup
        ###
        self.reporting_root_dir = os.path.join(os.path.dirname(sys.argv[0]), "reports")
        self.reporting_dir_format = reporting_dir_with_datetime
        self.reporting_backends = ConsoleBackend(), XmlBackend(), JsonBackend(), HtmlBackend()
    
        ###
        # Testsuites data
        ###
        self._testsuites = [ ]
        self._testsuites_by_id = { }
        self._tests_by_id = { }
        
        ###
        # Worker
        ###
        self._worker = None
        lemoncheesecake.worker.worker = None
    
    def set_worker(self, worker):
        self._worker = worker
        lemoncheesecake.worker.worker = worker
    
    def _load_testsuite(self, suite):
        # process suite
        if suite.id in self._testsuites_by_id:
            raise CannotLoadTestSuite("A test suite with id '%s' has been registered more than one time" % suite.id)
        self._testsuites_by_id[suite.id] = suite

        # process tests
        for test in suite.get_tests():
            if test.id in self._tests_by_id:
                raise CannotLoadTestSuite("A test with id '%s' has been registered more than one time" % test.id)
            self._tests_by_id[test.id] = test
        
        # process sub suites
        for sub_suite in suite.get_sub_testsuites():
            self._load_testsuite(sub_suite)
        
    def load_testsuites(self, suites):
        """Load TestSuite classes.
        
        :param suites: the test suites to load
        :type suites: list of TestSuite classes
        """
        for suite_klass in suites:
            suite = suite_klass()
            suite.load()
            self._load_testsuite(suite)
            self._testsuites.append(suite)
    
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
            elif isinstance(e, KeyboardInterrupt):
                rt.error("All tests have been interrupted manually by the user")
                self.abort_all_tests = True
            else:
                # FIXME; use exception instead of last implicit stacktrace
                stacktrace = traceback.format_exc()
                if not IS_PYTHON3:
                    stacktrace = stacktrace.decode("utf-8")
                rt.error("Caught unexpected exception while running test: " + stacktrace)

        rt.begin_before_suite(suite)

        if not self.abort_testsuite and not self.abort_all_tests:
            try:
                suite.before_suite()
            except Exception as e:
                handle_exception(e)
                self.abort_testsuite = suite
            except KeyboardInterrupt as e:
                handle_exception(e)
            
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
            except KeyboardInterrupt as e:
                handle_exception(e)
            
            try:
                suite.after_test(test.id)
            except Exception as e:
                handle_exception(e)
                rt.end_test()
                continue
            except KeyboardInterrupt as e:
                handle_exception(e)
            
            rt.end_test()
        
        for sub_suite in suite.get_sub_testsuites(filtered=True):
            self._run_testsuite(sub_suite)

        rt.begin_after_suite(suite)

        try:
            suite.after_suite()
        except Exception as e:
            handle_exception(e)
        except KeyboardInterrupt as e:
            handle_exception(e)
            
        rt.end_after_suite()
        
        # reset the abort suite flag
        if self.abort_testsuite == suite:
            self.abort_testsuite = None
        
    def run_testsuites(self, filter, report_dir):
        """Run the loaded test suites.
        
        :param filter: Only the test suites and tests that match the given filter will be run.
        :type filter: a Filter instance
        :param report_dir: The directory where the various reporting data files will be written. 
        If None, the default reporting dir mechanism will be used (see reporting_root_dir and
        reportin_dir_format attributes).
        :type report_dir: str
        """
        
        # retrieve test suites
        if filter.is_empty():
            testsuites = self._testsuites
        else:
            testsuites = []
            for suite in self._testsuites:
                suite.apply_filter(filter)
                if suite.has_selected_tests():
                    testsuites.append(suite)
            if not testsuites:
                raise LemonCheesecakeException("The test filter does not match any test.")
                
        # initialize runtime & global test variables
        if not report_dir:
            if not os.path.exists(self.reporting_root_dir):
                os.mkdir(self.reporting_root_dir)
            report_dir = self.reporting_root_dir
            report_dir += os.path.sep
            report_dir += self.reporting_dir_format(self.reporting_root_dir, time.time())
        os.mkdir(report_dir)
        if platform.system() != "Windows":
            symlink_path = os.path.join(os.path.dirname(report_dir), "..", "last_report")
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)
            os.symlink(report_dir, symlink_path)
        initialize_runtime(report_dir)
        rt = get_runtime()
        for backend in self.reporting_backends:
            rt.report_backends.append(backend)
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
        """Run the loaded test suites according to the command line parameters.
        
        :param args: the user CLI parameters
        :type args: the return value of the method parse_args of argparse.ArgumentParser
        """
        
        # init filter
        filter = Filter()
        filter.test_id = args.test_id
        filter.test_description = args.test_desc
        filter.testsuite_id = args.suite_id
        filter.testsuite_description = args.suite_desc
        filter.tags = args.tag
        filter.tickets = args.ticket
        
        # initialize worker using CLI args and run tests
        if self._worker:
            self._worker.cli_initialize(args)
        self.run_testsuites(filter, args.report_dir)
        
    def handle_cli(self):
        """Main method of the launcher: run the launcher according the CLI arguments (found in sys.argv).
        The method will exit with exit code 0 or 1 if anything goes wrong (NB: test failures or successes
        do not impact the exit code).
        """
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