'''
Created on Jan 24, 2016

@author: nicolas
'''

import os
import sys
import traceback

from lemoncheesecake.runtime import initialize_runtime, get_runtime
from lemoncheesecake.utils import IS_PYTHON3, get_distincts_in_list
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, FixtureError, \
    UserError, serialize_current_exception

class _Runner:
    def __init__(self, suites, fixture_registry, reporting_backends, report_dir, stop_on_failure=False):
        self.suites = suites
        self.fixture_registry = fixture_registry
        self.reporting_backends = reporting_backends
        self.report_dir = report_dir
        self.stop_on_failure = stop_on_failure

    def get_fixtures_with_dependencies_for_scope(self, direct_fixtures, scope):
        fixtures = []
        for fixture in direct_fixtures:
            fixtures.extend(self.fixture_registry.get_fixture_dependencies(fixture))
        fixtures.extend(direct_fixtures)
        return [f for f in get_distincts_in_list(fixtures) if self.fixture_registry.get_fixture_scope(f) == scope]

    def get_fixtures_to_be_executed_for_session_prerun(self):
        fixtures = []
        for suite in self.suites:
            fixtures.extend(suite.get_fixtures())
        return self.get_fixtures_with_dependencies_for_scope(get_distincts_in_list(fixtures), "session_prerun")

    def get_fixtures_to_be_executed_for_session(self):
        fixtures = []
        for suite in self.suites:
            fixtures.extend(suite.get_fixtures())
        return self.get_fixtures_with_dependencies_for_scope(get_distincts_in_list(fixtures), "session")

    def get_fixtures_to_be_executed_for_suite(self, suite):
        return self.get_fixtures_with_dependencies_for_scope(suite.get_fixtures(recursive=False), "suite")

    def get_fixtures_to_be_executed_for_test(self, test):
        return self.get_fixtures_with_dependencies_for_scope(test.get_params(), "test")

    def run_setup_funcs(self, funcs, failure_checker):
        teardown_funcs = []
        for setup_func, teardown_func in funcs:
            if setup_func:
                try:
                    setup_func()
                except (Exception, KeyboardInterrupt) as e:
                    self.handle_exception(e)
                    break
                else:
                    if failure_checker():
                        break
                    else:
                        teardown_funcs.append(teardown_func)
            else:
                teardown_funcs.append(teardown_func)
        return teardown_funcs

    def run_teardown_funcs(self, teardown_funcs):
        count = 0
        for teardown_func in teardown_funcs:
            if teardown_func:
                try:
                    teardown_func()
                except (Exception, KeyboardInterrupt) as e:
                    self.handle_exception(e)
                else:
                    count += 1
            else:
                count += 1
        return count

    def get_fixture_as_funcs(self, fixture):
        return [
            lambda: self.fixture_registry.execute_fixture(fixture),
            lambda: self.fixture_registry.teardown_fixture(fixture)
        ]

    def get_setup_suite_as_func(self, suite):
        setup_suite = suite.get_hook("setup_suite")
        if setup_suite == None:
            return None

        param_names = suite.get_hook_params("setup_suite")
        def func():
            params = self.fixture_registry.get_fixture_results_as_params(param_names)
            setup_suite(**params)

        return func

    def handle_exception(self, excp, suite=None):
        if isinstance(excp, AbortTest):
            self.session.log_error(str(excp))
        elif isinstance(excp, AbortSuite):
            self.session.log_error(str(excp))
            self.abort_suite = suite
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
        ###
        # Checker whether the test must be executed or not
        ###
        if test.disabled or suite.disabled:
            self.session.disable_test(test)
            return

        if self.abort_suite:
            self.session.skip_test(test, "Cannot execute this test: the tests of this test suite have been aborted.")
            return

        if self.abort_all_tests:
            self.session.skip_test(test, "Cannot execute this test: all tests have been aborted.")
            return

        ###
        # Begin test
        ###

        self.session.begin_test(test)

        ###
        # Setup test (setup and fixtures)
        ###
        test_setup_error = False
        setup_teardown_funcs = []
        teardown_funcs = []

        setup_teardown_funcs.append([
            (lambda: suite.get_hook("setup_test")(test.name)) if suite.has_hook("setup_test") else None,
            (lambda: suite.get_hook("teardown_test")(test.name)) if suite.has_hook("teardown_test") else None
        ])
        setup_teardown_funcs.extend([
            self.get_fixture_as_funcs(f) for f in self.get_fixtures_to_be_executed_for_test(test)
        ])

        if len(list(filter(lambda p: p[0] != None, setup_teardown_funcs))) > 0:
            self.session.begin_test_setup()
            teardown_funcs = self.run_setup_funcs(
                setup_teardown_funcs, lambda: self.session.current_test_data.has_failure()
            )
            self.session.end_test_setup()
            if len(teardown_funcs) != len(setup_teardown_funcs):
                test_setup_error = True
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]
        
        if self.stop_on_failure and test_setup_error:
            self.abort_all_tests = True

        ###
        # Run test:
        ###
        if not test_setup_error:
            test_func_params = self.fixture_registry.get_fixture_results_as_params(test.get_params())
            try:
                test.callback(**test_func_params)
            except (Exception, KeyboardInterrupt) as e:
                self.handle_exception(e, suite)

        ###
        # Teardown
        ###
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            self.session.begin_test_teardown()
            self.run_teardown_funcs(teardown_funcs)
            self.session.end_test_teardown()

        if self.stop_on_failure and self.session.current_test_data.has_failure():
            self.abort_all_tests = True

        self.session.end_test()

    def run_suite(self, suite):
        ###
        # Begin suite
        ###
        self.session.begin_suite(suite)

        ###
        # Setup suite (suites and fixtures)
        ###
        teardown_funcs = []
        if not self.abort_all_tests:
            setup_teardown_funcs = []
            setup_teardown_funcs.extend([
                self.get_fixture_as_funcs(f) for f in self.get_fixtures_to_be_executed_for_suite(suite)
            ])
            setup_teardown_funcs.append([
                self.get_setup_suite_as_func(suite), suite.get_hook("teardown_suite")
            ])

            if len(list(filter(lambda p: p[0] != None, setup_teardown_funcs))) > 0:
                self.session.begin_suite_setup()
                teardown_funcs = self.run_setup_funcs(
                    setup_teardown_funcs, lambda: self.session.current_suite_data.suite_setup.has_failure()
                )
                self.session.end_suite_setup()
                if len(teardown_funcs) != len(setup_teardown_funcs):
                    self.abort_suite = suite
            else:
                teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]
            
            if self.stop_on_failure and self.abort_suite:
                self.abort_all_tests = True

        ###
        # Run tests
        ###
        for test in suite.get_tests(filtered=True):
            self.run_test(test, suite)

        ###
        # Teardown suite
        ###
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            self.session.begin_suite_teardown()
            self.run_teardown_funcs(teardown_funcs)
            if self.stop_on_failure and self.session.current_suite_data.suite_teardown.has_failure():
                self.abort_all_tests = True
            self.session.end_suite_teardown()
        
        # reset the abort suite flag
        if self.abort_suite:
            self.abort_suite = None

        ###
        # Run sub suites
        ###
        for sub_suite in suite.get_suites(filtered=True):
            self.run_suite(sub_suite)

        ###
        # End of suite
        ###

        self.session.end_suite()

    def run_session(self):
        # initialize runtime & global test variables
        initialize_runtime(self.reporting_backends, self.report_dir)
        self.session = get_runtime()
        self.session.initialize_reporting_sessions()
        self.abort_all_tests = False
        self.abort_suite = None

        # init report information
        self.session.report.add_info("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:]))

        self.session.begin_tests()

        # setup test session
        setup_teardown_funcs = []
        teardown_funcs = []
        setup_teardown_funcs.extend([
            self.get_fixture_as_funcs(f) for f in self.get_fixtures_to_be_executed_for_session()
        ])

        if len(list(filter(lambda p: p[0] != None, setup_teardown_funcs))) > 0:
            self.session.begin_test_session_setup()
            teardown_funcs = self.run_setup_funcs(
                setup_teardown_funcs, lambda: self.session.report.test_session_setup.has_failure()
            )
            self.session.end_test_session_setup()
            if len(teardown_funcs) != len(setup_teardown_funcs):
                self.abort_all_tests = True
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]

        # run suites
        for suite in self.suites:
            self.run_suite(suite)

        # teardown_test_session handling
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            self.session.begin_test_session_teardown()
            self.run_teardown_funcs(teardown_funcs)
            self.session.end_test_session_teardown()

        self.session.end_tests()

    def run(self):
        executed_fixtures = []

        errors = []
        for fixture in self.get_fixtures_to_be_executed_for_session_prerun():
            try:
                self.fixture_registry.execute_fixture(fixture)
            except UserError:
                raise
            except (Exception, KeyboardInterrupt):
                errors.append("Got the following exception when executing fixture '%s' (scope 'session_prerun')%s" % (
                    fixture, serialize_current_exception(show_stacktrace=True)
                ))
                break
            executed_fixtures.append(fixture)

        if not errors:
            self.run_session()

        for fixture in executed_fixtures:
            try:
                self.fixture_registry.teardown_fixture(fixture)
            except UserError:
                raise
            except (Exception, KeyboardInterrupt):
                errors.append("Got the following exception on fixture '%s' teardown (scope 'session_prerun')%s" % (
                    fixture, serialize_current_exception(show_stacktrace=True)
                ))

        if errors:
            raise FixtureError("\n".join(errors))
        
        return self.session.is_successful()

def run_suites(suites, fixture_registry, reporting_backends, report_dir, stop_on_failure=False):
    """
    Run suites.

    - suites: a list of already loaded suites (see lemoncheesecake.loader.load_suites)
    - reporting_backends: instance of reporting backends that will be used to report test results
    - report_dir: an existing directory where report files will be stored
    """
    runner = _Runner(suites, fixture_registry, reporting_backends, report_dir, stop_on_failure)
    return runner.run() # TODO: return a Report instance instead
