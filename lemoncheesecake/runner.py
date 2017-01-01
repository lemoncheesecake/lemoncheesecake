'''
Created on Jan 24, 2016

@author: nicolas
'''

import sys
import traceback

from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.exceptions import AbortTest, AbortTestSuite, AbortAllTests, ProgrammingError

class _Runner:
    def __init__(self, testsuites, workers, reporting_backends, report_dir):
        self.testsuites = testsuites
        self.workers = workers
        self.reporting_backends = reporting_backends
        self.report_dir = report_dir

    def get_workers_with_hook(self, hook_name):
        return list(filter(lambda b: b.has_hook(hook_name), self.workers.values()))
    
    def handle_exception(self, excp, suite=None):        
        if isinstance(excp, AbortTest):
            self.session.log_error(str(excp))
        elif isinstance(excp, AbortTestSuite):
            self.session.log_error(str(excp))
            self.abort_testsuite = suite
        elif isinstance(excp, AbortAllTests):
            self.session.log_error(str(excp))
            self.abort_all_tests = True
        elif isinstance(excp, KeyboardInterrupt):
            self.session.log_error("All tests have been interrupted manually by the user")
            self.abort_all_tests = True
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if not IS_PYTHON3:
                stacktrace = stacktrace.decode("utf-8", "replace")
            self.session.log_error("Caught unexpected exception while running test: " + stacktrace)
    
    def run_testsuite(self, suite):
        # set workers
        for worker_name, worker in self.workers.items():
            if hasattr(suite, worker_name):
                raise ProgrammingError("Cannot set worker '%s' into testsuite '%s', it already has an attribute with that name" % (
                    worker_name, suite
                ))
            setattr(suite, worker_name, worker)
    
        self.session.begin_suite(suite)

        if suite.has_hook("before_suite"):
            self.session.begin_before_suite()
            if not self.abort_testsuite and not self.abort_all_tests:
                try:
                    suite.before_suite()
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.abort_testsuite = suite
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
            suite_data = self.session.report.get_suite(suite.id)
            if suite_data.before_suite.has_failure():
                self.abort_testsuite = suite
            self.session.end_before_suite()
        
        for test in suite.get_tests(filtered=True):
            self.session.begin_test(test)
            if self.abort_testsuite:
                self.session.log_error("Cannot execute this test: the tests of this test suite have been aborted.")
                self.session.end_test()
                continue
            if self.abort_all_tests:
                self.session.log_error("Cannot execute this test: all tests have been aborted.")
                self.session.end_test()
                continue

            try:
                if suite.has_hook("before_test"):
                    suite.before_test(test.id)
                test.callback(suite)
            except Exception as e:
                self.handle_exception(e, suite)
                self.session.end_test()
                continue
            except KeyboardInterrupt as e:
                self.handle_exception(e, suite)
            
            if suite.has_hook("after_test"):
                try:
                    suite.after_test(test.id)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.session.end_test()
                    continue
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
            
            self.session.end_test()
        
        for sub_suite in suite.get_sub_testsuites(filtered=True):
            self.run_testsuite(sub_suite)

        if suite.has_hook("after_suite"):
            self.session.begin_after_suite()
            try:
                suite.after_suite()
            except Exception as e:
                self.handle_exception(e, suite)
            except KeyboardInterrupt as e:
                self.handle_exception(e, suite)
            self.session.end_after_suite()
        
        self.session.end_suite()
        
        # reset the abort suite flag
        if self.abort_testsuite == suite:
            self.abort_testsuite = None
        
    def run(self):
        # initialize runtime & global test variables
        initialize_runtime(self.workers, self.reporting_backends, self.report_dir)
        self.session = get_runtime()
        self.session.initialize_reporting_sessions()
        self.abort_all_tests = False
        self.abort_testsuite = None
        
        # init report information
        self.session.report.add_info("Command line", " ".join(sys.argv))
        
        self.session.begin_tests()
        
        # workers hook before_all_tests handling
        workers = self.get_workers_with_hook("before_all_tests")
        if workers:
            self.session.begin_worker_hook_before_all_tests()
            for worker in workers:
                try:
                    worker.before_all_tests()
                except Exception as e:
                    self.handle_exception(e)
                    self.abort_all_tests = True
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
            self.session.end_worker_hook_before_all_tests()
            if self.session.report.before_all_tests.has_failure():
                self.abort_all_tests = True
        
        # run tests
        for suite in self.testsuites:
            self.run_testsuite(suite)
        
        # workers after_test hook
        workers = self.get_workers_with_hook("after_all_tests")
        if workers:
            self.session.begin_worker_hook_after_all_tests()
            for worker in workers:
                try:
                    worker.after_all_tests()
                except Exception as e:
                    self.handle_exception(e)
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
            self.session.end_worker_hook_after_all_tests()
    
        self.session.end_tests()

def run_testsuites(testsuites, workers, reporting_backends, report_dir):
    """
    Run testsuites.
    
    - testsuites: a list of already loaded testsuites (see lemoncheesecake.loader.load_testsuites)
    - workers: a dict where keys are worker names and values worker instances
    - reporting_backends: instance of reporting backends that will be used to report test results
    - report_dir: an existing directory where report files will be stored 
    """
    runner = _Runner(testsuites, workers, reporting_backends, report_dir)
    runner.run()