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
    def __init__(self, testsuites, fixture_registry, workers, reporting_backends, report_dir):
        self.testsuites = testsuites
        self.fixture_registry = fixture_registry
        self.workers = workers
        self.reporting_backends = reporting_backends
        self.report_dir = report_dir

    def get_workers_with_hook(self, hook_name):
        return list(filter(lambda b: b.has_hook(hook_name), self.workers.values()))
    
    def get_fixtures_with_dependencies_for_scope(self, direct_fixtures, scope):
        fixtures = set(direct_fixtures)
        for fixture in direct_fixtures:
            fixtures.update(self.fixture_registry.get_fixture_dependencies(fixture))
        return [f for f in fixtures if self.fixture_registry.get_fixture_scope(f) == scope]
    
    def get_fixtures_to_be_executed_for_session(self):
        fixtures = set()
        for testsuite in self.testsuites:
            fixtures.update(testsuite.get_fixtures())
        return self.get_fixtures_with_dependencies_for_scope(fixtures, "session")    

    def get_fixtures_to_be_executed_for_testsuite(self, testsuite):
        return self.get_fixtures_with_dependencies_for_scope(testsuite.get_fixtures(), "testsuite")

    def get_fixtures_to_be_executed_for_test(self, test):
        return self.get_fixtures_with_dependencies_for_scope(test.get_params(), "test")
    
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
    
    def run_test(self, test, suite):
        self.session.begin_test(test)
        
        if self.abort_testsuite:
            self.session.log_error("Cannot execute this test: the tests of this test suite have been aborted.")
            self.session.end_test()
            return
        if self.abort_all_tests:
            self.session.log_error("Cannot execute this test: all tests have been aborted.")
            self.session.end_test()
            return

        # test setup:
        fixtures = self.get_fixtures_to_be_executed_for_test(test)
        if suite.has_hook("setup_test") or fixtures:
            self.session.begin_test_setup()
            if suite.has_hook("setup_test"):
                try:
                    suite.setup_test(test.id)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.session.end_test()
                    return
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
        
            for fixture in fixtures:
                try:
                    self.fixture_registry.execute_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.session.end_test()
                    return
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
            self.session.end_test_setup()

        # run test:
        test_func_params = self.fixture_registry.get_fixture_results_as_params(test.get_params())
        try:
            test.callback(suite, **test_func_params)
        except Exception as e:
            self.handle_exception(e, suite)
            self.session.end_test()
            return
        except KeyboardInterrupt as e:
            self.handle_exception(e, suite)
        
        # teardown test:
        if suite.has_hook("teardown_test") or fixtures:
            self.session.begin_test_teardown()
            if suite.has_hook("teardown_test"):
                try:
                    suite.teardown_test(test.id)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.session.end_test()
                    return
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)

            for fixture in fixtures:
                if not self.fixture_registry.is_fixture_executed(fixture):
                    continue
                try:
                    self.fixture_registry.teardown_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.session.end_test()
                    return
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
            self.session.end_test_teardown()
        
        self.session.end_test()

    def run_testsuite(self, suite):
        # set workers
        for worker_name, worker in self.workers.items():
            if hasattr(suite, worker_name):
                raise ProgrammingError("Cannot set worker '%s' into testsuite '%s', it already has an attribute with that name" % (
                    worker_name, suite
                ))
            setattr(suite, worker_name, worker)
    
        self.session.begin_suite(suite)

        fixtures = self.get_fixtures_to_be_executed_for_testsuite(suite)
        if suite.has_hook("setup_suite") or fixtures:
            self.session.begin_suite_setup()
            if suite.has_hook("setup_suite"):
                if not self.abort_testsuite and not self.abort_all_tests:
                    try:
                        suite.setup_suite()
                    except Exception as e:
                        self.handle_exception(e, suite)
                        self.abort_testsuite = suite
                    except KeyboardInterrupt as e:
                        self.handle_exception(e, suite)

            for fixture in fixtures:
                try:
                    self.fixture_registry.execute_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e, suite)
                    self.abort_testsuite = suite
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
                
            suite_data = self.session.report.get_suite(suite.id)
            if suite_data.suite_setup.has_failure():
                self.abort_testsuite = suite
            self.session.end_suite_setup()
        
        for test in suite.get_tests(filtered=True):
            self.run_test(test, suite)
            
        for sub_suite in suite.get_sub_testsuites(filtered=True):
            self.run_testsuite(sub_suite)

        if suite.has_hook("teardown_suite") or fixtures:
            self.session.begin_suite_teardown()
            if suite.has_hook("teardown_suite"):
                try:
                    suite.teardown_suite()
                except Exception as e:
                    self.handle_exception(e, suite)
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)

            for fixture in fixtures:
                if not self.fixture_registry.is_fixture_executed(fixture):
                    continue
                try:
                    self.fixture_registry.teardown_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e, suite)
                except KeyboardInterrupt as e:
                    self.handle_exception(e, suite)
            
            self.session.end_suite_teardown()
        
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
        
        # setup test session (workers and fixtures)
        workers = self.get_workers_with_hook("setup_test_session")
        fixtures = self.get_fixtures_to_be_executed_for_session()
        if workers or fixtures:
            self.session.begin_test_session_setup()
            for worker in workers:
                try:
                    worker.setup_test_session()
                except Exception as e:
                    self.handle_exception(e)
                    self.abort_all_tests = True
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
                
            for fixture in fixtures:
                try:
                    self.fixture_registry.execute_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e)
                    self.abort_all_tests = True
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
                
            self.session.end_test_session_setup()

            if self.session.report.test_session_setup.has_failure():
                self.abort_all_tests = True
        
        # run tests
        for suite in self.testsuites:
            self.run_testsuite(suite)
        
        # teardown_test_session handling
        workers = self.get_workers_with_hook("teardown_test_session")
        if workers or fixtures:
            self.session.begin_test_session_teardown()
            for worker in workers:
                try:
                    worker.teardown_test_session()
                except Exception as e:
                    self.handle_exception(e)
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
            
            for fixture in fixtures:
                if not self.fixture_registry.is_fixture_executed(fixture):
                    continue
                try:
                    self.fixture_registry.teardown_fixture(fixture)
                except Exception as e:
                    self.handle_exception(e)
                except KeyboardInterrupt as e:
                    self.handle_exception(e)
                
            self.session.end_test_session_teardown()
    
        self.session.end_tests()

def get_reserved_fixtures():
    return []

def run_testsuites(testsuites, fixture_registry, workers, reporting_backends, report_dir):
    """
    Run testsuites.
    
    - testsuites: a list of already loaded testsuites (see lemoncheesecake.loader.load_testsuites)
    - workers: a dict where keys are worker names and values worker instances
    - reporting_backends: instance of reporting backends that will be used to report test results
    - report_dir: an existing directory where report files will be stored 
    """
    runner = _Runner(testsuites, fixture_registry, workers, reporting_backends, report_dir)
    runner.run()