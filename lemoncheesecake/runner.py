'''
Created on Jan 24, 2016

@author: nicolas
'''

import os
import sys
import traceback

from lemoncheesecake.utils import IS_PYTHON3, get_distincts_in_list
from lemoncheesecake.runtime import *
from lemoncheesecake.runtime import initialize_runtime
from lemoncheesecake.reporting import Report, initialize_report_writer, initialize_reporting_backends
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, FixtureError, \
    UserError, serialize_current_exception
from lemoncheesecake import events


def _get_fixtures_used_in_suite(suite):
    fixtures = suite.get_fixtures()

    for test in suite.get_tests():
        fixtures.extend(test.get_fixtures())

    return get_distincts_in_list(fixtures)


def _get_fixtures_used_in_suite_recursively(suite):
    fixtures = _get_fixtures_used_in_suite(suite)

    for sub_suite in suite.get_suites():
        fixtures.extend(_get_fixtures_used_in_suite_recursively(sub_suite))

    return get_distincts_in_list(fixtures)


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
            fixtures.extend(_get_fixtures_used_in_suite_recursively(suite))
        return self.get_fixtures_with_dependencies_for_scope(get_distincts_in_list(fixtures), "session_prerun")

    def get_fixtures_to_be_executed_for_session(self):
        fixtures = []
        for suite in self.suites:
            fixtures.extend(_get_fixtures_used_in_suite_recursively(suite))
        return self.get_fixtures_with_dependencies_for_scope(get_distincts_in_list(fixtures), "session")

    def get_fixtures_to_be_executed_for_suite(self, suite):
        return self.get_fixtures_with_dependencies_for_scope(_get_fixtures_used_in_suite(suite), "suite")

    def get_fixtures_to_be_executed_for_test(self, test):
        return self.get_fixtures_with_dependencies_for_scope(test.get_fixtures(), "test")

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

        fixtures_names = suite.get_hook_params("setup_suite")
        def func():
            fixtures = self.fixture_registry.get_fixture_results(fixtures_names)
            setup_suite(**fixtures)

        return func

    def inject_fixtures_into_suite(self, suite):
        fixture_names = suite.get_injected_fixture_names()
        fixtures = self.fixture_registry.get_fixture_results(fixture_names)
        suite.inject_fixtures(fixtures)

    def handle_exception(self, excp, suite=None):
        if isinstance(excp, AbortTest):
            log_error(str(excp))
        elif isinstance(excp, AbortSuite):
            log_error(str(excp))
            self.abort_suite = suite
        elif isinstance(excp, AbortAllTests):
            log_error(str(excp))
            self.abort_all_tests = True
        elif isinstance(excp, KeyboardInterrupt):
            log_error("All tests have been interrupted manually by the user")
            self.abort_all_tests = True
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if not IS_PYTHON3:
                stacktrace = stacktrace.decode("utf-8", "replace")
            log_error("Caught unexpected exception while running test: " + stacktrace)

    def run_test(self, test, suite):
        ###
        # Checker whether the test must be executed or not
        ###
        if test.disabled or suite.disabled:
            events.fire("on_disabled_test", test)
            return

        if self.abort_suite:
            events.fire("on_skipped_test", test, "Cannot execute this test: the tests of this test suite have been aborted.")
            return

        if self.abort_all_tests:
            events.fire("on_skipped_test", test, "Cannot execute this test: all tests have been aborted.")
            return

        ###
        # Begin test
        ###

        events.fire("on_test_beginning", test)

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
            events.fire("on_test_setup_beginning", test)
            teardown_funcs = self.run_setup_funcs(
                setup_teardown_funcs, lambda: self.session.current_test_data.has_failure()
            )
            if len(teardown_funcs) != len(setup_teardown_funcs):
                test_setup_error = True
            events.fire("on_test_setup_ending", test, not test_setup_error)
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]
        
        if self.stop_on_failure and test_setup_error:
            self.abort_all_tests = True

        ###
        # Run test:
        ###
        if not test_setup_error:
            test_func_params = self.fixture_registry.get_fixture_results(test.get_fixtures())
            try:
                test.callback(**test_func_params)
            except (Exception, KeyboardInterrupt) as e:
                self.handle_exception(e, suite)

        ###
        # Teardown
        ###
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            events.fire("on_test_teardown_beginning", test)
            self.run_teardown_funcs(teardown_funcs)
            events.fire("on_test_teardown_ending", test, not self.session.current_test_data.has_failure())

        if self.stop_on_failure and self.session.current_test_data.has_failure():
            self.abort_all_tests = True

        events.fire("on_test_ending", test, "failed" if self.session.has_pending_failure else "passed")

    def run_suite(self, suite):
        ###
        # Begin suite
        ###
        events.fire("on_suite_beginning", suite)

        ###
        # Setup suite (suites and fixtures)
        ###
        teardown_funcs = []
        if not self.abort_all_tests:
            setup_teardown_funcs = []
            # first, fixtures must be executed
            setup_teardown_funcs.extend([
                self.get_fixture_as_funcs(f) for f in self.get_fixtures_to_be_executed_for_suite(suite)
            ])
            # then, fixtures must be injected into suite
            setup_teardown_funcs.append((lambda: self.inject_fixtures_into_suite(suite), None))
            # and at the end, the setup_suite hook of the suite will be called
            setup_teardown_funcs.append([
                self.get_setup_suite_as_func(suite), suite.get_hook("teardown_suite")
            ])

            if len(list(filter(lambda p: p[0] != None, setup_teardown_funcs))) > 0:
                events.fire("on_suite_setup_beginning", suite)
                teardown_funcs = self.run_setup_funcs(
                    setup_teardown_funcs, lambda: self.session.current_suite_data.suite_setup.has_failure()
                )
                if len(teardown_funcs) != len(setup_teardown_funcs):
                    self.abort_suite = suite
                events.fire("on_suite_setup_ending", suite, self.abort_suite is None)
            else:
                teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]
            
            if self.stop_on_failure and self.abort_suite:
                self.abort_all_tests = True

        ###
        # Run tests
        ###
        for test in suite.get_tests():
            self.run_test(test, suite)

        ###
        # Teardown suite
        ###
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            events.fire("on_suite_teardown_beginning", suite)
            self.run_teardown_funcs(teardown_funcs)
            if self.stop_on_failure and self.session.current_suite_data.suite_teardown.has_failure():
                self.abort_all_tests = True
            events.fire("on_suite_teardown_ending", suite, self.abort_all_tests is False)
        
        # reset the abort suite flag
        if self.abort_suite:
            self.abort_suite = None

        ###
        # Run sub suites
        ###
        for sub_suite in suite.get_suites():
            self.run_suite(sub_suite)

        ###
        # End of suite
        ###

        events.fire("on_suite_ending", suite)

    def run_session(self):
        # initialize runtime & global test variables
        report = Report()
        report.add_info("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:]))
        self.session = initialize_report_writer(report)
        initialize_runtime(self.report_dir, report, self.fixture_registry)
        initialize_reporting_backends(self.reporting_backends, self.report_dir, report)
        self.abort_all_tests = False
        self.abort_suite = None

        events.fire("on_tests_beginning", report)

        # setup test session
        setup_teardown_funcs = []
        teardown_funcs = []
        setup_teardown_funcs.extend([
            self.get_fixture_as_funcs(f) for f in self.get_fixtures_to_be_executed_for_session()
        ])

        if len(list(filter(lambda p: p[0] != None, setup_teardown_funcs))) > 0:
            events.fire("on_test_session_setup_beginning")
            teardown_funcs = self.run_setup_funcs(
                setup_teardown_funcs, lambda: self.session.report.test_session_setup.has_failure()
            )
            if len(teardown_funcs) != len(setup_teardown_funcs):
                self.abort_all_tests = True
            events.fire("on_test_session_setup_ending", self.abort_all_tests is False)
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] != None]

        # run suites
        for suite in self.suites:
            self.run_suite(suite)

        # teardown_test_session handling
        if len(list(filter(lambda f: f != None, teardown_funcs))) > 0:
            events.fire("on_test_session_teardown_beginning")
            self.run_teardown_funcs(teardown_funcs)
            events.fire("on_test_session_teardown_ending", self.session.has_pending_failure)

        events.fire("on_tests_ending", report)

    def run(self):
        executed_fixtures = []

        # setup pre_session fixtures
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

        # teardown pre_session fixtures
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
    return runner.run()  # TODO: return a Report instance instead
