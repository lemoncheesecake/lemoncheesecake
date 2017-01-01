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

from lemoncheesecake.loader import load_testsuites
from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.testsuite import filter as testsuitefilter
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake import reporting
from lemoncheesecake.exceptions import LemonCheesecakeException, InvalidMetadataError, AbortTest, AbortTestSuite, AbortAllTests, ProgrammingError

__all__ = ("Launcher", "get_launcher_abspath", "get_abspath_from_launcher")

COMMAND_RUN = "run"

def archive_dirname_datetime(ts, archives_dir):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(ts))

# TODO: create two different functions
def report_dir_with_archives(top_dir, dirname_callback):
    archives_dir = os.path.join(top_dir, "reports")
    
    if platform.system() == "Windows":
        report_dir = os.path.join(top_dir, "report")
        if os.path.exists(report_dir):
            if not os.path.exists(archives_dir):
                os.mkdir(archives_dir)
            os.rename(
                report_dir, os.path.join(archives_dir, dirname_callback(os.path.getctime(report_dir), archives_dir))
            )
        os.mkdir(report_dir)
        
    else:
        if not os.path.exists(archives_dir):
            os.mkdir(archives_dir)
        
        report_dirname = dirname_callback(time.time(), archives_dir)
    
        report_dir = os.path.join(archives_dir, report_dirname)
        os.mkdir(report_dir)
    
        symlink_path = os.path.join(os.path.dirname(report_dir), "..", "report")
        if os.path.lexists(symlink_path):
            os.unlink(symlink_path)
        os.symlink(report_dir, symlink_path)
    
    return report_dir

def get_launcher_abspath():
    return os.path.abspath(os.path.dirname(sys.argv[0]))

def get_abspath_from_launcher(path):
    return path if os.path.isabs(path) else os.path.join(get_launcher_abspath(), path)

class Launcher:
    def __init__(self, report_top_dir):
        self.cli_parser = argparse.ArgumentParser()

        ###
        # CLI setup
        ###
        testsuitefilter.add_filter_args_to_cli_parser(self.cli_parser)
        self.cli_parser.add_argument("--report-dir", "-r", required=False, help="Directory where report data will be stored")
        self.cli_parser.add_argument("--reporting", nargs="+", required=False,
            help="The list of reporting backends to use"
        )
        self.cli_parser.add_argument("--enable-reporting", nargs="+", required=False,
            help="The list of reporting backends to add (to base backends)"
        )
        self.cli_parser.add_argument("--disable-reporting", nargs="+", required=False,
            help="The list of reporting backends to remove (from base backends)"
        )
        
        ###
        # Working data
        ###
        self._report_top_dir = report_top_dir
        self._report_dir_creation_callback = lambda: report_dir_with_archives(archive_dirname_datetime)
        self._testsuites = [ ]
        self._workers = {}
        self.metadata_policy = MetadataPolicy()
        self._reporting_backends = {}
        self._active_reporting_backends_names = []
        
        ###
        # Hooks
        ###
        self.before_test_run_hook = None
        self.after_test_run_hook = None
            
    def get_cli_args_parser(self):
        return self.cli_parser

    def set_report_dir_creation_callback(self, callback):
        self._report_dir_creation_callback = callback

    def set_testsuites(self, suites):
        "Set already loaded testsuites into the test launcher."
        self._testsuites = suites
    
    def add_worker(self, worker_name, worker):
        self._workers[worker_name] = worker

    def get_workers_with_hook(self, hook_name):
        return list(filter(lambda b: b.has_hook(hook_name), self._workers.values()))
    
    def add_reporting_backend(self, backend, is_active=True):
        self._reporting_backends[backend.name] = backend
        if is_active:
            self._active_reporting_backends_names.append(backend.name)
    
    def _handle_exception(self, excp, suite=None):
        rt = get_runtime()
            
        if isinstance(excp, AbortTest):
            rt.log_error(str(excp))
        elif isinstance(excp, AbortTestSuite):
            rt.log_error(str(excp))
            self.abort_testsuite = suite
        elif isinstance(excp, AbortAllTests):
            rt.log_error(str(excp))
            self.abort_all_tests = True
        elif isinstance(excp, KeyboardInterrupt):
            rt.log_error("All tests have been interrupted manually by the user")
            self.abort_all_tests = True
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if not IS_PYTHON3:
                stacktrace = stacktrace.decode("utf-8", "replace")
            rt.log_error("Caught unexpected exception while running test: " + stacktrace)
    
    def _run_testsuite(self, suite):
        rt = get_runtime()

        # set workers
        for worker_name, worker in self._workers.items():
            if hasattr(suite, worker_name):
                raise ProgrammingError("Cannot set worker '%s' into testsuite '%s', it already has an attribute with that name" % (
                    worker_name, suite
                ))
            setattr(suite, worker_name, worker)
    
        rt.begin_suite(suite)

        if suite.has_hook("before_suite"):
            rt.begin_before_suite()
            if not self.abort_testsuite and not self.abort_all_tests:
                try:
                    suite.before_suite()
                except Exception as e:
                    self._handle_exception(e, suite)
                    self.abort_testsuite = suite
                except KeyboardInterrupt as e:
                    self._handle_exception(e, suite)
            suite_data = rt.report.get_suite(suite.id)
            if suite_data.before_suite.has_failure():
                self.abort_testsuite = suite
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
                if suite.has_hook("before_test"):
                    suite.before_test(test.id)
                test.callback(suite)
            except Exception as e:
                self._handle_exception(e, suite)
                rt.end_test()
                continue
            except KeyboardInterrupt as e:
                self._handle_exception(e, suite)
            
            if suite.has_hook("after_test"):
                try:
                    suite.after_test(test.id)
                except Exception as e:
                    self._handle_exception(e, suite)
                    rt.end_test()
                    continue
                except KeyboardInterrupt as e:
                    self._handle_exception(e, suite)
            
            rt.end_test()
        
        for sub_suite in suite.get_sub_testsuites(filtered=True):
            self._run_testsuite(sub_suite)

        if suite.has_hook("after_suite"):
            rt.begin_after_suite()
            try:
                suite.after_suite()
            except Exception as e:
                self._handle_exception(e, suite)
            except KeyboardInterrupt as e:
                self._handle_exception(e, suite)
            rt.end_after_suite()
        
        rt.end_suite()
        
        # reset the abort suite flag
        if self.abort_testsuite == suite:
            self.abort_testsuite = None
        
    def run_testsuites(self, filter, reporting_backend_names, report_dir):
        """Run the loaded test suites.
        
        :param filter: Only the test suites and tests that match the given filter will be run.
        :type filter: a Filter instance
        :param report_dir: The directory where the various report data files will be written. 
        If None, the default report dir mechanism will be used (see report_root_dir and
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
                
        # create report dir
        if report_dir:
            os.mkdir(report_dir)
        else:
            report_dir = self._report_dir_creation_callback(self._report_top_dir)
        
        if self.before_test_run_hook:
            self.before_test_run_hook(report_dir)

        # initialize runtime & global test variables
        initialize_runtime(
            self._workers, [self._reporting_backends[name] for name in reporting_backend_names], report_dir
        )
        rt = get_runtime()
        rt.initialize_reporting_sessions()
        self.abort_all_tests = False
        self.abort_testsuite = None
        
        # init report information
        rt.report.add_info("Command line", " ".join(sys.argv))
        
        rt.begin_tests()
        
        # workers hook before_all_tests handling
        workers = self.get_workers_with_hook("before_all_tests")
        if workers:
            rt.begin_worker_hook_before_all_tests()
            for worker in workers:
                try:
                    worker.before_all_tests()
                except Exception as e:
                    self._handle_exception(e)
                    self.abort_all_tests = True
                except KeyboardInterrupt as e:
                    self._handle_exception(e)
            rt.end_worker_hook_before_all_tests()
            if rt.report.before_all_tests.has_failure():
                self.abort_all_tests = True
        
        # run tests
        for suite in testsuites:
            self._run_testsuite(suite)
        
        # workers after_test hook
        workers = self.get_workers_with_hook("after_all_tests")
        if workers:
            rt.begin_worker_hook_after_all_tests()
            for worker in workers:
                try:
                    worker.after_all_tests()
                except Exception as e:
                    self._handle_exception(e)
                except KeyboardInterrupt as e:
                    self._handle_exception(e)
            rt.end_worker_hook_after_all_tests()
    
        rt.end_tests()

        if self.after_test_run_hook:
            self.after_test_run_hook(report_dir)
    
    def cli_run_testsuites(self, args):
        """Run the loaded test suites according to the command line parameters.
        
        :param args: the user CLI parameters
        :type args: the return value of the method parse_args of argparse.ArgumentParser
        """
        
        # init filter
        filter = testsuitefilter.get_filter_from_cli_args(args)
                
        # report backends
        reporting_backend_names = set(self._active_reporting_backends_names)
        if args.reporting:
            reporting_backend_names = set(args.reporting)
        if args.enable_reporting:
            for backend in args.enable_reporting:
                reporting_backend_names.add(backend)
        if args.disable_reporting:
            for backend in args.disable_reporting:
                reporting_backend_names.remove(backend)
        
        # initialize workers using CLI args and run tests
        for worker in self._workers.values():
            worker.cli_initialize(args)
        self.run_testsuites(filter, reporting_backend_names, args.report_dir)
        
    def handle_cli(self):
        """Main method of the launcher: run the launcher according the CLI arguments (found in sys.argv).
        The method will exit with exit code 0 or 1 if anything goes wrong (NB: test failures or successes
        do not impact the exit code).
        """
        try:
            args = self.cli_parser.parse_args()
            self.cli_run_testsuites(args)
        except LemonCheesecakeException as e:
            return e
        
        return 0