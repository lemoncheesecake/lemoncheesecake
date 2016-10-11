'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import os, os.path
import platform
import time
import argparse
import traceback

import lemoncheesecake # for worker access
from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.launcher.filter import Filter
from lemoncheesecake import reporting
from lemoncheesecake.exceptions import LemonCheesecakeException, InvalidMetadataError, AbortTest, AbortTestSuite, AbortAllTests

__all__ = ("Launcher", "get_launcher_abspath", "get_abspath_from_launcher")

COMMAND_RUN = "run"

def reporting_dir_with_datetime(report_rootdir, t):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(t))

def property_value(value):
    splitted = value.split(":")
    if len(splitted) != 2:
        raise ValueError()
    return splitted

def get_launcher_abspath():
    return os.path.abspath(os.path.dirname(sys.argv[0]))

def get_abspath_from_launcher(path):
    return path if os.path.isabs(path) else os.path.join(get_launcher_abspath(), path)

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
        self.cli_run_parser.add_argument("--property", "-m", nargs="+", type=property_value, default=[], help="Filters on test & test suite property")
        self.cli_run_parser.add_argument("--url", "-u", nargs="+", default=[], help="Filters on test & test suite url names")
        self.cli_run_parser.add_argument("--report-dir", "-r", required=False, help="Directory where reporting data will be stored")
        
        ###
        # Default reporting setup when no --report-dir has been setup
        ###
        self.reporting_root_dir = os.path.join(os.path.dirname(sys.argv[0]), "reports")
        self.reporting_dir_format = reporting_dir_with_datetime
    
        ###
        # Testsuites data
        ###
        self._testsuites = [ ]
        self._testsuites_by_id = { }
        self._tests_by_id = { }
            
    def set_worker(self, worker):
        "Set the worker that will be used in the testsuites"
        lemoncheesecake.set_worker(worker)
    
    def _load_testsuite(self, suite, property_validator):
        # process suite
        if suite.id in self._testsuites_by_id:
            raise InvalidMetadataError("A test suite with id '%s' has been registered more than one time" % suite.id)
        if property_validator:
            property_validator.check_suite_compliance(suite)
        self._testsuites_by_id[suite.id] = suite

        # process tests
        for test in suite.get_tests():
            if test.id in self._tests_by_id:
                raise InvalidMetadataError("A test with id '%s' has been registered more than one time" % test.id)
            if property_validator:
                property_validator.check_test_compliance(test)
            self._tests_by_id[test.id] = test
        
        # process sub suites
        for sub_suite in suite.get_sub_testsuites():
            self._load_testsuite(sub_suite, property_validator)
        
    def load_testsuites(self, suites, property_validator=None):
        """Load testsuites classes into the launcher.
        
        - testsuite classes get instantiated into objects
        - sanity checks are performed (among which unicity constraints)
        - test and testsuites properties are checked using property_validator (PropertyValidator instance)
          is supplied
        """
        for suite_klass in suites:
            suite = suite_klass()
            suite.load()
            self._load_testsuite(suite, property_validator)
            self._testsuites.append(suite)
    
    def _run_testsuite(self, suite):
        rt = get_runtime()
                
        def handle_exception(e):
            if isinstance(e, AbortTest):
                rt.log_error(str(e))
            elif isinstance(e, AbortTestSuite):
                rt.log_error(str(e))
                self.abort_testsuite = suite
            elif isinstance(e, AbortAllTests):
                rt.log_error(str(e))
                self.abort_all_tests = True
            elif isinstance(e, KeyboardInterrupt):
                rt.log_error("All tests have been interrupted manually by the user")
                self.abort_all_tests = True
            else:
                # FIXME; use exception instead of last implicit stacktrace
                stacktrace = traceback.format_exc()
                if not IS_PYTHON3:
                    stacktrace = stacktrace.decode("utf-8")
                rt.log_error("Caught unexpected exception while running test: " + stacktrace)

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
                rt.log_error("Cannot execute this test: the tests of this test suite have been aborted.")
                rt.end_test()
                continue
            if self.abort_all_tests:
                rt.log_error("Cannot execute this test: all tests have been aborted.")
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
            if os.path.lexists(symlink_path):
                os.unlink(symlink_path)
            os.symlink(report_dir, symlink_path)
        initialize_runtime(report_dir)
        rt = get_runtime()
        rt.init_reporting_backends()
        self.abort_all_tests = False
        self.abort_testsuite = None
        
        # init report information
        rt.reporting_data.add_info("Command line", " ".join(sys.argv))
        
        if lemoncheesecake.worker:
            lemoncheesecake.worker.before_tests()
        
        # run tests
        rt.begin_tests()
        for suite in testsuites:
            self._run_testsuite(suite)
        rt.end_tests()
        
        if lemoncheesecake.worker:
            lemoncheesecake.worker.after_tests()

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
        filter.properties = dict(args.property)
        filter.url_names = args.url
        
        # initialize worker using CLI args and run tests
        if lemoncheesecake.worker:
            lemoncheesecake.worker.cli_initialize(args)
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