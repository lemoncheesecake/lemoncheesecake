'''
Created on Jan 24, 2016

@author: nicolas
'''

import os
import sys
import traceback
import threading
from multiprocessing.dummy import Pool

from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.runtime import *
from lemoncheesecake.runtime import initialize_runtime, set_runtime_location, is_location_successful
from lemoncheesecake.reporting import Report, initialize_report_writer, initialize_reporting_backends
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, FixtureError, \
    UserError, serialize_current_exception
from lemoncheesecake import events
from lemoncheesecake.testtree import TreeLocation, flatten_tests


class _Runner:
    def __init__(self, suites, fixture_registry, reporting_backends, report_dir, stop_on_failure=False, nb_threads=1):
        self.suites = suites
        self.fixture_registry = fixture_registry
        self.reporting_backends = reporting_backends
        self.report_dir = report_dir
        self.stop_on_failure = stop_on_failure
        self.nb_threads = nb_threads
        # attributes set at runtime:
        self._report = None
        self._session = None
        self._abort_all_tests = False
        self._abort_suite = None

    def run_setup_funcs(self, funcs, location):
        teardown_funcs = []
        for setup_func, teardown_func in funcs:
            if setup_func:
                try:
                    setup_func()
                except (Exception, KeyboardInterrupt) as e:
                    self.handle_exception(e)
                    break
                else:
                    if not is_location_successful(location):
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

    def get_setup_suite_as_func(self, suite, scheduled_fixtures):
        setup_suite = suite.get_hook("setup_suite")
        if setup_suite is None:
            return None

        fixtures_names = suite.get_hook_params("setup_suite")
        def func():
            fixtures = scheduled_fixtures.get_fixture_results(fixtures_names)
            setup_suite(**fixtures)

        return func

    def inject_fixtures_into_suite(self, suite, scheduled_fixtures):
        suite.inject_fixtures(
            scheduled_fixtures.get_fixture_results(
                suite.get_injected_fixture_names()
            )
        )

    def handle_exception(self, excp, suite=None):
        if isinstance(excp, AbortTest):
            log_error(str(excp))
        elif isinstance(excp, AbortSuite):
            log_error(str(excp))
            self._abort_suite = suite
        elif isinstance(excp, AbortAllTests):
            log_error(str(excp))
            self._abort_all_tests = True
        elif isinstance(excp, KeyboardInterrupt):
            self._abort_all_tests = True
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if not IS_PYTHON3:
                stacktrace = stacktrace.decode("utf-8", "replace")
            log_error("Caught unexpected exception while running test: " + stacktrace)

    @staticmethod
    def _check_event_failure():
        exception, serialized_exception = events.get_pending_failure()
        if exception:
            raise exception.__class__(serialized_exception)

    def _begin_test(self, test):
        self._check_event_failure()
        events.fire(events.TestStartEvent(test))
        set_runtime_location(TreeLocation.in_test(test))

    def _end_test(self, test):
        self._check_event_failure()
        events.fire(events.TestEndEvent(test))

    def _begin_test_setup(self, test):
        self._check_event_failure()
        events.fire(events.TestSetupStartEvent(test))
        set_step("Setup test")

    def _end_test_setup(self, test, outcome):
        self._check_event_failure()
        events.fire(events.TestSetupEndEvent(test, outcome))

    def _begin_test_teardown(self, test):
        self._check_event_failure()
        events.fire(events.TestTeardownStartEvent(test))
        set_step("Teardown test")

    def _end_test_teardown(self, test, outcome):
        self._check_event_failure()
        events.fire(events.TestTeardownEndEvent(test, outcome))

    def run_test(self, test, suite_scheduled_fixtures):
        ###
        # Checker whether the test must be executed or not
        ###
        if test.is_disabled():
            events.fire(events.TestDisabledEvent(test, ""))
            return

        if self._abort_suite:
            events.fire(events.TestSkippedEvent(test, "Cannot execute this test: the tests of this test suite have been aborted."))
            return

        if self._abort_all_tests:
            events.fire(events.TestSkippedEvent(test, "Cannot execute this test: all tests have been aborted."))
            return

        ###
        # Begin test
        ###

        self._begin_test(test)

        ###
        # Setup test (setup and fixtures)
        ###
        suite = test.parent_suite
        test_setup_error = False
        setup_teardown_funcs = []

        setup_teardown_funcs.append([
            (lambda: suite.get_hook("setup_test")(test.name)) if suite.has_hook("setup_test") else None,
            (lambda: suite.get_hook("teardown_test")(test.name)) if suite.has_hook("teardown_test") else None
        ])
        scheduled_fixtures = self.fixture_registry.get_fixtures_scheduled_for_test(test, suite_scheduled_fixtures)
        setup_teardown_funcs.extend(scheduled_fixtures.get_setup_teardown_pairs())

        if len(list(filter(lambda p: p[0] is not None, setup_teardown_funcs))) > 0:
            self._begin_test_setup(test)
            teardown_funcs = self.run_setup_funcs(setup_teardown_funcs, TreeLocation.in_test(test))
            if len(teardown_funcs) != len(setup_teardown_funcs):
                test_setup_error = True
            self._end_test_setup(test, not test_setup_error)
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] is not None]
        
        if self.stop_on_failure and test_setup_error:
            self._abort_all_tests = True

        ###
        # Run test:
        ###
        if not test_setup_error:
            test_func_params = scheduled_fixtures.get_fixture_results(test.get_fixtures())
            set_step(test.description)
            try:
                test.callback(**test_func_params)
            except (Exception, KeyboardInterrupt) as e:
                self.handle_exception(e, suite)

        ###
        # Teardown
        ###
        if len(list(filter(lambda f: f is not None, teardown_funcs))) > 0:
            self._begin_test_teardown(test)
            self.run_teardown_funcs(teardown_funcs)
            self._end_test_teardown(test, is_location_successful(TreeLocation.in_test(test)))

        if self.stop_on_failure and not is_location_successful(TreeLocation.in_test(test)):
            self._abort_all_tests = True

        self._end_test(test)

    def _begin_suite(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteStartEvent(suite))

    def _end_suite(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteEndEvent(suite))

    def _begin_suite_setup(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteSetupStartEvent(suite))
        set_runtime_location(TreeLocation.in_suite_setup(suite))
        set_step("Setup suite")

    def _end_suite_setup(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteSetupEndEvent(suite))

    def _begin_suite_teardown(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteTeardownStartEvent(suite))
        set_runtime_location(TreeLocation.in_suite_teardown(suite))
        set_step("Teardown suite")

    def _end_suite_teardown(self, suite):
        self._check_event_failure()
        events.fire(events.SuiteTeardownEndEvent(suite))

    def run_suite(self, suite, session_scheduled_fixtures):
        ###
        # Begin suite
        ###
        self._begin_suite(suite)

        ###
        # Setup suite (suites and fixtures)
        ###
        teardown_funcs = []
        if not self._abort_all_tests:
            setup_teardown_funcs = []
            # first, fixtures must be executed
            scheduled_fixtures = self.fixture_registry.get_fixtures_scheduled_for_suite(suite, session_scheduled_fixtures)
            setup_teardown_funcs.extend(scheduled_fixtures.get_setup_teardown_pairs())
            # then, fixtures must be injected into suite
            setup_teardown_funcs.append((lambda: self.inject_fixtures_into_suite(suite, scheduled_fixtures), None))
            # and at the end, the setup_suite hook of the suite will be called
            setup_teardown_funcs.append([
                self.get_setup_suite_as_func(suite, scheduled_fixtures), suite.get_hook("teardown_suite")
            ])

            if len(list(filter(lambda p: p[0] is not None, setup_teardown_funcs))) > 0:
                self._begin_suite_setup(suite)
                teardown_funcs = self.run_setup_funcs(setup_teardown_funcs, TreeLocation.in_suite_setup(suite))
                if len(teardown_funcs) != len(setup_teardown_funcs):
                    self._abort_suite = suite
                self._end_suite_setup(suite)
            else:
                teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] is not None]
            
            if self.stop_on_failure and self._abort_suite:
                self._abort_all_tests = True
        else:
            # if self._abort_all_tests is true, then scheduled_fixtures won't be used by run_test
            scheduled_fixtures = None

        ###
        # Run tests
        ###
        pool = Pool(self.nb_threads)
        try:
            pool.map(lambda test: self.run_test(test, scheduled_fixtures), suite.get_tests())
        except (Exception, KeyboardInterrupt) as excp:
            self.handle_exception(excp, suite=suite)
        pool.close()

        ###
        # Teardown suite
        ###
        if len(list(filter(lambda f: f is not None, teardown_funcs))) > 0:
            self._begin_suite_teardown(suite)
            self.run_teardown_funcs(teardown_funcs)
            if self.stop_on_failure and not is_location_successful(TreeLocation.in_suite_teardown(suite)):
                self._abort_all_tests = True
            self._end_suite_teardown(suite)

        # reset the abort suite flag
        if self._abort_suite:
            self._abort_suite = None

        ###
        # Run sub suites
        ###
        for sub_suite in suite.get_suites():
            self.run_suite(sub_suite, session_scheduled_fixtures)

        ###
        # End of suite
        ###

        self._end_suite(suite)

    def _begin_test_session(self):
        events.fire(events.TestSessionStartEvent(self._report))

    def _end_test_session(self):
        events.fire(events.TestSessionEndEvent(self._report))

    def _begin_test_session_setup(self):
        events.fire(events.TestSessionSetupStartEvent())
        set_runtime_location(TreeLocation.in_test_session_setup())
        set_step("Setup test session")

    def _end_test_session_setup(self):
        events.fire(events.TestSessionSetupEndEvent())

    def _begin_test_session_teardown(self):
        events.fire(events.TestSessionTeardownStartEvent())
        set_runtime_location(TreeLocation.in_test_session_teardown())
        set_step("Teardown test session")

    def _end_test_session_teardown(self):
        events.fire(events.TestSessionTeardownEndEvent())

    def run_session(self, prerun_session_scheduled_fixtures):
        # initialize runtime & global test variables
        self._report = Report()
        self._report.add_info("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:]))
        self._session = initialize_report_writer(self._report)
        nb_tests = len(list(flatten_tests(self.suites)))
        initialize_runtime(self.report_dir, self._report, prerun_session_scheduled_fixtures)
        initialize_reporting_backends(
            self.reporting_backends, self.report_dir, self._report,
            parallel=self.nb_threads > 1 and nb_tests > 1
        )
        self._abort_all_tests = False
        self._abort_suite = None

        # start event handler thread
        event_handler_thread = threading.Thread(target=events.handler_loop)
        event_handler_thread.start()

        self._begin_test_session()

        # setup test session
        scheduled_fixtures = self.fixture_registry.get_fixtures_scheduled_for_session(
            self.suites, prerun_session_scheduled_fixtures
        )
        setup_teardown_funcs = scheduled_fixtures.get_setup_teardown_pairs()

        if len(list(filter(lambda p: p[0] is not None, setup_teardown_funcs))) > 0:
            self._begin_test_session_setup()
            teardown_funcs = self.run_setup_funcs(setup_teardown_funcs, TreeLocation.in_test_session_setup())
            if len(teardown_funcs) != len(setup_teardown_funcs):
                self._abort_all_tests = True
            self._end_test_session_setup()
        else:
            teardown_funcs = [p[1] for p in setup_teardown_funcs if p[1] is not None]

        # run suites
        for suite in self.suites:
            self.run_suite(suite, scheduled_fixtures)

        # teardown_test_session handling
        if len(list(filter(lambda f: f is not None, teardown_funcs))) > 0:
            self._begin_test_session_teardown()
            self.run_teardown_funcs(teardown_funcs)
            self._end_test_session_teardown()

        self._end_test_session()

        # wait for event handler to finish
        events.end_of_events()
        event_handler_thread.join()
        self._check_event_failure()

    def run(self):
        fixture_teardowns = []

        # setup pre_session fixtures
        errors = []
        scheduled_fixtures = self.fixture_registry.get_fixtures_scheduled_for_session_prerun(self.suites)
        for setup, teardown in scheduled_fixtures.get_setup_teardown_pairs():
            try:
                setup()
            except UserError:
                raise
            except (Exception, KeyboardInterrupt):
                errors.append("Got the following exception when executing fixture (scope 'session_prerun')%s" % (
                    serialize_current_exception(show_stacktrace=True)
                ))
                break
            fixture_teardowns.append(teardown)

        if not errors:
            self.run_session(scheduled_fixtures)

        # teardown pre_session fixtures
        for teardown in fixture_teardowns:
            try:
                teardown()
            except UserError:
                raise
            except (Exception, KeyboardInterrupt):
                errors.append("Got the following exception on fixture teardown (scope 'session_prerun')%s" % (
                    serialize_current_exception(show_stacktrace=True)
                ))

        if errors:
            raise FixtureError("\n".join(errors))

        stats = self._report.get_stats()
        return stats.is_successful()


def run_suites(suites, fixture_registry, reporting_backends, report_dir, stop_on_failure=False, nb_threads=1):
    """
    Run suites.

    - suites: a list of already loaded suites (see lemoncheesecake.loader.load_suites)
    - reporting_backends: instance of reporting backends that will be used to report test results
    - report_dir: an existing directory where report files will be stored
    """
    runner = _Runner(suites, fixture_registry, reporting_backends, report_dir, stop_on_failure, nb_threads)
    return runner.run()  # TODO: return a Report instance instead
