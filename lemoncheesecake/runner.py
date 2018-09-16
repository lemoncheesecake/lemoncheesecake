'''
Created on Jan 24, 2016

@author: nicolas
'''

import os
import sys
import traceback
import threading
import itertools

from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.runtime import *
from lemoncheesecake.runtime import initialize_runtime, set_runtime_location, is_location_successful
from lemoncheesecake.reporting import Report, initialize_report_writer, initialize_reporting_backends
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, FixtureError, \
    UserError, serialize_current_exception
from lemoncheesecake import events
from lemoncheesecake.testtree import TreeLocation, flatten_tests
from lemoncheesecake.task import BaseTask, run_tasks


class RunContext(object):
    def __init__(self, stop_on_failure, fixture_registry):
        self.stop_on_failure = stop_on_failure
        self.fixture_registry = fixture_registry
        self._abort_tests = False
        self._aborted_suites = set()

    def abort_suite(self, suite):
        self._aborted_suites.add(suite)

    def is_suite_aborted(self, suite):
        return suite in self._aborted_suites

    def abort_session(self):
        self._abort_tests = True

    def is_session_aborted(self):
        return self._abort_tests

    def handle_exception(self, excp, suite=None):
        if isinstance(excp, AbortTest):
            log_error(str(excp))
        elif isinstance(excp, AbortSuite):
            log_error(str(excp))
            self.abort_suite(suite)
        elif isinstance(excp, AbortAllTests):
            log_error(str(excp))
            self.abort_session()
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if not IS_PYTHON3:
                stacktrace = stacktrace.decode("utf-8", "replace")
            log_error("Caught unexpected exception while running test: " + stacktrace)

    def run_setup_funcs(self, funcs, location):
        teardown_funcs = []
        for setup_func, teardown_func in funcs:
            if setup_func:
                try:
                    setup_func()
                except Exception as e:
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
                except Exception as e:
                    self.handle_exception(e)
                else:
                    count += 1
            else:
                count += 1
        return count


class TestTask(BaseTask):
    def __init__(self, test, suite_scheduled_fixtures, dependency=None):
        BaseTask.__init__(self)
        self.test = test
        self.suite_scheduled_fixtures = suite_scheduled_fixtures
        self.dependency = dependency

    def get_dependencies(self):
        return (self.dependency,) if self.dependency else ()

    def abort(self, context, reason=""):
        events.fire(events.TestSkippedEvent(self.test, reason))

    def run(self, context):
        suite = self.test.parent_suite

        ###
        # Checker whether the test must be executed or not
        ###
        if self.test.is_disabled():
            events.fire(events.TestDisabledEvent(self.test, ""))
            return

        if context.is_suite_aborted(suite):
            self.abort(context, "Cannot execute this test: the tests of this test suite have been aborted.")
            return

        if context.is_session_aborted():
            self.abort(context, "Cannot execute this test: all tests have been aborted.")
            return

        ###
        # Begin test
        ###
        events.fire(events.TestStartEvent(self.test))
        set_runtime_location(TreeLocation.in_test(self.test))

        ###
        # Setup test (setup and fixtures)
        ###
        test_setup_error = False
        setup_teardown_funcs = list()

        if suite.has_hook("setup_test"):
            def setup_test_wrapper():
                suite.get_hook("setup_test")(self.test)
        else:
            setup_test_wrapper = None

        if suite.has_hook("teardown_test"):
            def teardown_test_wrapper():
                status_so_far = "passed" if is_location_successful(TreeLocation.in_test(self.test)) else "failed"
                suite.get_hook("teardown_test")(self.test, status_so_far)
        else:
            teardown_test_wrapper = None

        setup_teardown_funcs.append((setup_test_wrapper, teardown_test_wrapper))
        scheduled_fixtures = context.fixture_registry.get_fixtures_scheduled_for_test(
            self.test, self.suite_scheduled_fixtures
        )
        setup_teardown_funcs.extend(scheduled_fixtures.get_setup_teardown_pairs())

        if any(setup for setup, _ in setup_teardown_funcs):
            events.fire(events.TestSetupStartEvent(self.test))
            set_step("Setup test")
            teardown_funcs = context.run_setup_funcs(setup_teardown_funcs, TreeLocation.in_test(self.test))
            if len(teardown_funcs) != len(setup_teardown_funcs):
                test_setup_error = True
            events.fire(events.TestSetupEndEvent(self.test, not test_setup_error))
        else:
            teardown_funcs = [teardown for _, teardown in setup_teardown_funcs if teardown]

        if context.stop_on_failure and test_setup_error:
            context.abort_session()

        ###
        # Run test:
        ###
        if not test_setup_error:
            test_func_params = scheduled_fixtures.get_fixture_results(self.test.get_fixtures())
            set_step(self.test.description)
            try:
                self.test.callback(**test_func_params)
            except Exception as e:
                context.handle_exception(e, suite)

        ###
        # Teardown
        ###
        if any(teardown_funcs):
            events.fire(events.TestTeardownStartEvent(self.test))
            set_step("Teardown test")
            context.run_teardown_funcs(teardown_funcs)
            events.fire(events.TestTeardownEndEvent(self.test, is_location_successful(TreeLocation.in_test(self.test))))

        if context.stop_on_failure and not is_location_successful(TreeLocation.in_test(self.test)):
            context.abort_session()

        events.fire(events.TestEndEvent(self.test))

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.test.path)


def build_test_task(test, suite_scheduled_fixtures, dependency):
    return TestTask(test, suite_scheduled_fixtures, dependency)


def build_suite_tasks(
        suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task,
        parent_suite_beginning_task=None):
    ###
    # Build suite beginning task
    ###
    suite_beginning_task = build_suite_beginning_task(
        suite, list(filter(bool, (test_session_setup_task, parent_suite_beginning_task)))
    )

    ###
    # Build suite setup task (if any)
    ###
    suite_scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_suite(
        suite, session_scheduled_fixtures
    )
    suite_setup_task = build_suite_initialization_task(suite, suite_scheduled_fixtures, (suite_beginning_task,))

    ###
    # Build test tasks
    ###
    test_dependency = suite_setup_task if suite_setup_task else suite_beginning_task
    test_tasks = [
        build_test_task(test, suite_scheduled_fixtures, test_dependency)
        for test in suite.get_tests()
    ]

    ###
    # Build suite teardown task (if any)
    ###
    suite_teardown_task = build_suite_teardown_task(suite, suite_setup_task, test_tasks)

    ###
    # Build sub suite tasks
    ###
    sub_suite_tasks = []
    for sub_suite in suite.get_suites():
        sub_suite_tasks.extend(
            build_suite_tasks(
                sub_suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task, suite_beginning_task
            )
        )

    ###
    # Build suite ending task
    ###
    suite_ending_dependencies = []
    suite_ending_dependencies.extend(test_tasks)
    if suite_teardown_task:
        suite_ending_dependencies.append(suite_teardown_task)
    suite_ending_dependencies.extend(
        task for task in sub_suite_tasks if isinstance(task, SuiteEndingTask) and task.suite in suite.get_suites()
    )
    suite_ending_task = build_suite_ending_task(suite, suite_ending_dependencies)

    ###
    # Return tasks != None
    ###
    task_iter = itertools.chain(
        (suite_beginning_task,),
        (suite_setup_task,), test_tasks, (suite_teardown_task,), sub_suite_tasks,
        (suite_ending_task,)
    )
    return list(filter(bool, task_iter))


class SuiteBeginningTask(BaseTask):
    def __init__(self, suite, dependencies):
        BaseTask.__init__(self)
        self.suite = suite
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies

    def run(self, context):
        events.fire(events.SuiteStartEvent(self.suite))

    abort = run

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.suite.path)


def build_suite_beginning_task(suite, dependencies):
    return SuiteBeginningTask(suite, dependencies)


class SuiteInitializationTask(BaseTask):
    def __init__(self, suite, setup_teardown_funcs, dependencies):
        BaseTask.__init__(self)
        self.suite = suite
        self.setup_teardown_funcs = setup_teardown_funcs
        self._dependencies = dependencies
        self.teardown_funcs = []

    def get_dependencies(self):
        return self._dependencies

    @staticmethod
    def begin_suite_setup(suite):
        events.fire(events.SuiteSetupStartEvent(suite))
        set_runtime_location(TreeLocation.in_suite_setup(suite))
        set_step("Setup suite")

    @staticmethod
    def end_suite_setup(suite):
        events.fire(events.SuiteSetupEndEvent(suite))

    def run(self, context):
        if context.is_session_aborted():
            return

        if any(setup for setup, _ in self.setup_teardown_funcs):
            SuiteInitializationTask.begin_suite_setup(self.suite)
            self.teardown_funcs = context.run_setup_funcs(
                self.setup_teardown_funcs, TreeLocation.in_suite_setup(self.suite)
            )
            if len(self.teardown_funcs) != len(self.setup_teardown_funcs):
                context.abort_suite(self.suite)
            SuiteInitializationTask.end_suite_setup(self.suite)
        else:
            self.teardown_funcs = [teardown for _, teardown in self.setup_teardown_funcs if teardown]

        if context.stop_on_failure and context.is_suite_aborted(self.suite):
            context.abort_session()

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.suite.path)


def wrap_setup_suite(suite, scheduled_fixtures):
    setup_suite = suite.get_hook("setup_suite")
    if setup_suite is None:
        return None

    fixtures_names = suite.get_hook_params("setup_suite")
    def wrapper():
        fixtures = scheduled_fixtures.get_fixture_results(fixtures_names)
        setup_suite(**fixtures)

    return wrapper


def build_suite_initialization_task(suite, scheduled_fixtures, dependencies):
    setup_teardown_funcs = []

    if not scheduled_fixtures.is_empty():
        setup_teardown_funcs.extend(scheduled_fixtures.get_setup_teardown_pairs())

    if suite.get_injected_fixture_names():
        setup_teardown_funcs.append((
            lambda: suite.inject_fixtures(scheduled_fixtures.get_fixture_results(suite.get_injected_fixture_names())),
            None
        ))

    if suite.has_hook("setup_suite") or suite.has_hook("teardown_suite"):
        setup_teardown_funcs.append([
            wrap_setup_suite(suite, scheduled_fixtures),
            suite.get_hook("teardown_suite")
        ])

    return SuiteInitializationTask(suite, setup_teardown_funcs, dependencies) if setup_teardown_funcs else None


class SuiteEndingTask(BaseTask):
    def __init__(self, suite, dependencies):
        BaseTask.__init__(self)
        self.suite = suite
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies

    def run(self, context):
        events.fire(events.SuiteEndEvent(self.suite))

    abort = run

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.suite.path)


def build_suite_ending_task(suite, dependencies):
    return SuiteEndingTask(suite, dependencies)


class SuiteTeardownTask(BaseTask):
    def __init__(self, suite, suite_setup_task, dependencies):
        BaseTask.__init__(self)
        self.suite = suite
        self.suite_setup_task = suite_setup_task
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies

    @staticmethod
    def begin_suite_teardown(suite):
        events.fire(events.SuiteTeardownStartEvent(suite))
        set_runtime_location(TreeLocation.in_suite_teardown(suite))
        set_step("Teardown suite")

    @staticmethod
    def end_suite_teardown(suite):
        events.fire(events.SuiteTeardownEndEvent(suite))

    def run(self, context):
        if any(self.suite_setup_task.teardown_funcs):
            SuiteTeardownTask.begin_suite_teardown(self.suite)
            context.run_teardown_funcs(self.suite_setup_task.teardown_funcs)
            if context.stop_on_failure and not is_location_successful(TreeLocation.in_suite_teardown(self.suite)):
                context.abort_session()
            SuiteTeardownTask.end_suite_teardown(self.suite)

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.suite.path)


def build_suite_teardown_task(suite, suite_setup_task, dependencies):
    return SuiteTeardownTask(suite, suite_setup_task, dependencies) if suite_setup_task else None


class TestSessionSetupTask(BaseTask):
    def __init__(self, scheduled_fixtures):
        BaseTask.__init__(self)
        self.scheduled_fixtures = scheduled_fixtures
        self.teardown_funcs = []

    @staticmethod
    def begin_test_session_setup():
        events.fire(events.TestSessionSetupStartEvent())
        set_runtime_location(TreeLocation.in_test_session_setup())
        set_step("Setup test session")

    @staticmethod
    def end_test_session_setup():
        events.fire(events.TestSessionSetupEndEvent())

    def run(self, context):
        setup_teardown_funcs = self.scheduled_fixtures.get_setup_teardown_pairs()

        if any(setup for setup, _ in setup_teardown_funcs):
            TestSessionSetupTask.begin_test_session_setup()
            self.teardown_funcs = context.run_setup_funcs(setup_teardown_funcs, TreeLocation.in_test_session_setup())
            if len(self.teardown_funcs) != len(setup_teardown_funcs):
                context.abort_session()
            TestSessionSetupTask.end_test_session_setup()
        else:
            self.teardown_funcs = [teardown for _, teardown in setup_teardown_funcs if teardown]


def build_test_session_setup_task(scheduled_fixtures):
    return TestSessionSetupTask(scheduled_fixtures) if not scheduled_fixtures.is_empty() else None


class TestSessionTeardownTask(BaseTask):
    def __init__(self, test_session_setup_task, dependencies):
        BaseTask.__init__(self)
        self.test_session_setup_task = test_session_setup_task
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies

    @staticmethod
    def begin_test_session_teardown():
        events.fire(events.TestSessionTeardownStartEvent())
        set_runtime_location(TreeLocation.in_test_session_teardown())
        set_step("Teardown test session")

    @staticmethod
    def end_test_session_teardown():
        events.fire(events.TestSessionTeardownEndEvent())

    def run(self, context):
        if any(self.test_session_setup_task.teardown_funcs):
            TestSessionTeardownTask.begin_test_session_teardown()
            context.run_teardown_funcs(self.test_session_setup_task.teardown_funcs)
            TestSessionTeardownTask.end_test_session_teardown()


def build_test_session_teardown_task(test_session_setup_task, dependencies):
    return TestSessionTeardownTask(test_session_setup_task, dependencies) if test_session_setup_task else None


def build_tasks(suites, fixture_registry, session_scheduled_fixtures):
    ###
    # Build test session setup task
    ###
    test_session_setup_task = build_test_session_setup_task(session_scheduled_fixtures)

    ###
    # Build suite tasks
    ###
    suite_tasks = []
    for suite in suites:
        suite_tasks.extend(
            build_suite_tasks(suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task)
        )

    ###
    # Build test session teardown task
    ###
    if test_session_setup_task:
        test_session_teardown_dependencies = [
            task for task in suite_tasks if isinstance(task, SuiteEndingTask) and task.suite in suites
        ]
        test_session_teardown_task = build_test_session_teardown_task(
            test_session_setup_task, test_session_teardown_dependencies
        )
    else:
        test_session_teardown_task = None

    ###
    # Return tasks != None
    ###
    task_iter = itertools.chain((test_session_setup_task,), suite_tasks, (test_session_teardown_task,))
    return list(filter(bool, task_iter))


def watchdog():
    exception, serialized_exception = events.get_pending_failure()
    if exception:
        return exception.__class__, serialized_exception
    else:
        return None, None


def run_session(suites, fixture_registry, prerun_session_scheduled_fixtures, reporting_backends, report_dir,
                stop_on_failure=False, nb_threads=1):
    # initialize runtime & global test variables
    report = Report()
    report.nb_threads = nb_threads
    report.add_info("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:]))
    session = initialize_report_writer(report)
    nb_tests = len(list(flatten_tests(suites)))
    initialize_runtime(report_dir, report, prerun_session_scheduled_fixtures)
    initialize_reporting_backends(
        reporting_backends, report_dir, report, parallel=nb_threads > 1 and nb_tests > 1
    )

    # build tasks and run context
    session_scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_session(
        suites, prerun_session_scheduled_fixtures
    )
    tasks = build_tasks(suites, fixture_registry, session_scheduled_fixtures)
    context = RunContext(stop_on_failure, fixture_registry)

    # start event handler thread
    event_handler_thread = threading.Thread(target=events.handler_loop)
    event_handler_thread.start()

    try:
        events.fire(events.TestSessionStartEvent(report))
        run_tasks(tasks, context, nb_threads, watchdog)
        events.fire(events.TestSessionEndEvent(report))
    finally:
        # wait for event handler to finish
        events.end_of_events()
        event_handler_thread.join()

    exception, serialized_exception = events.get_pending_failure()
    if exception:
        raise exception.__class__(serialized_exception)

    return report


def run_suites(suites, fixture_registry, reporting_backends, report_dir, stop_on_failure=False, nb_threads=1):
    fixture_teardowns = []

    # setup pre_session fixtures
    errors = []
    scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_session_prerun(suites)
    for setup, teardown in scheduled_fixtures.get_setup_teardown_pairs():
        try:
            setup()
        except UserError:
            raise
        except Exception:
            errors.append("Got the following exception when executing fixture (scope 'session_prerun')%s" % (
                serialize_current_exception(show_stacktrace=True)
            ))
            break
        fixture_teardowns.append(teardown)

    if not errors:
        report = run_session(
            suites, fixture_registry, scheduled_fixtures,
            reporting_backends, report_dir, stop_on_failure=stop_on_failure, nb_threads=nb_threads
        )
    else:
        report = None

    # teardown pre_session fixtures
    for teardown in fixture_teardowns:
        try:
            teardown()
        except UserError:
            raise
        except Exception:
            errors.append("Got the following exception on fixture teardown (scope 'session_prerun')%s" % (
                serialize_current_exception(show_stacktrace=True)
            ))

    if errors:
        raise FixtureError("\n".join(errors))

    return report.is_successful() if report else False
