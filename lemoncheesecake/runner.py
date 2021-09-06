'''
Created on Jan 24, 2016

@author: nicolas
'''

import traceback
import itertools

import six

from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, LemoncheesecakeException, \
    UserError, TaskFailure, serialize_current_exception
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.reporting import ReportLocation
from lemoncheesecake.task import BaseTask, TaskContext, run_tasks
from lemoncheesecake.fixture import initialize_fixture_cache


class RunContext(TaskContext):
    def __init__(self, session, fixture_registry, force_disabled, stop_on_failure):
        super(RunContext, self).__init__()
        self.session = session
        self.fixture_registry = fixture_registry
        self.force_disabled = force_disabled
        self.stop_on_failure = stop_on_failure
        self._aborted_session = False
        self._aborted_suites = set()

    def handle_exception(self, excp, suite=None):
        if isinstance(excp, AbortTest):
            self.session.log_error("The test has been aborted: %s" % excp)
        elif isinstance(excp, AbortSuite):
            self.session.log_error("The suite has been aborted: %s" % excp)
            self._aborted_suites.add(suite)
        elif isinstance(excp, AbortAllTests):
            self.session.log_error("All tests have been aborted: %s" % excp)
            self._aborted_session = True
        else:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if six.PY2:
                stacktrace = stacktrace.decode("utf-8", "replace")
            self.session.log_error("Caught unexpected exception while running test: " + stacktrace)

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
                    if not self.session.is_successful(location):
                        break
                    else:
                        teardown_funcs.append(teardown_func)
            else:
                teardown_funcs.append(teardown_func)
        return teardown_funcs

    def run_teardown_funcs(self, teardown_funcs):
        for teardown_func in teardown_funcs:
            if teardown_func:
                try:
                    teardown_func()
                except Exception as e:
                    self.handle_exception(e)

    def enable_task_abort(self):
        super(RunContext, self).enable_task_abort()
        self.session.aborted = True

    def is_task_to_be_skipped(self, task):
        # check for error in base implementation
        skip_reason = super(RunContext, self).is_task_to_be_skipped(task)
        if skip_reason:
            return skip_reason

        # check for error in event handling
        exception, _ = self.session.event_manager.get_pending_failure()
        if exception is not None:
            return str(exception)

        # check for test session abort
        if self._aborted_session:
            return "tests have been aborted"

        # check for suite abort
        if isinstance(task, TestTask):
            if task.test.parent_suite in self._aborted_suites:
                return "the tests of this test suite have been aborted"

        # check for --stop-on-failure
        if self.stop_on_failure and not self.session.is_successful():
            return "tests have been aborted on --stop-on-failure"

        return None


class TestTask(BaseTask):
    def __init__(self, test, suite_scheduled_fixtures, dependency=None):
        BaseTask.__init__(self)
        self.test = test
        self.suite_scheduled_fixtures = suite_scheduled_fixtures
        self.dependencies = [dependency] if dependency else []

    def get_on_success_dependencies(self):
        return self.dependencies

    def _is_test_disabled(self, context):
        return self.test.is_disabled() and not context.force_disabled

    def _handle_disabled_test(self, context):
        disabled = self.test.is_disabled()
        disabled_reason = disabled if isinstance(disabled, six.string_types) else None
        context.session.disable_test(self.test, disabled_reason)

    def skip(self, context, reason=None):
        if self._is_test_disabled(context):
            self._handle_disabled_test(context)
        else:
            context.session.skip_test(self.test, "Test skipped because %s" % reason if reason else None)

    @staticmethod
    def _prepare_test_args(test, scheduled_fixtures):
        args = {}
        for arg_name in test.get_arguments():
            if arg_name in test.parameters:
                args[arg_name] = test.parameters[arg_name]
            else:
                args[arg_name] = scheduled_fixtures.get_fixture_result(arg_name)

        return args

    def run(self, context):
        ###
        # Checker whether the test must be executed or not
        ###
        if self._is_test_disabled(context):
            self._handle_disabled_test(context)
            return

        ###
        # Begin test
        ###
        context.session.start_test(self.test)

        ###
        # Setup test (setup and fixtures)
        ###
        suite = self.test.parent_suite

        if suite.has_hook("setup_test"):
            def setup_test_wrapper():
                suite.get_hook("setup_test")(self.test)
        else:
            setup_test_wrapper = None

        if suite.has_hook("teardown_test"):
            def teardown_test_wrapper():
                status_so_far = "passed" if context.session.is_successful(ReportLocation.in_test(self.test)) else "failed"
                suite.get_hook("teardown_test")(self.test, status_so_far)
        else:
            teardown_test_wrapper = None

        setup_teardown_funcs = list()
        setup_teardown_funcs.append((setup_test_wrapper, teardown_test_wrapper))
        scheduled_fixtures = context.fixture_registry.get_fixtures_scheduled_for_test(
            self.test, self.suite_scheduled_fixtures
        )
        setup_teardown_funcs.extend(scheduled_fixtures.get_setup_teardown_pairs())

        context.session.set_step("Setup test")

        if any(setup for setup, _ in setup_teardown_funcs):
            teardown_funcs = context.run_setup_funcs(setup_teardown_funcs, ReportLocation.in_test(self.test))
        else:
            teardown_funcs = [teardown for _, teardown in setup_teardown_funcs if teardown]

        ###
        # Run test:
        ###
        if context.session.is_successful(ReportLocation.in_test(self.test)):
            test_args = self._prepare_test_args(self.test, scheduled_fixtures)
            context.session.set_step(self.test.description)
            try:
                self.test.callback(**test_args)
            except Exception as e:
                context.handle_exception(e, suite)

        ###
        # Teardown
        ###
        if any(teardown_funcs):
            context.session.set_step("Teardown test")
            context.run_teardown_funcs(teardown_funcs)

        context.session.end_test(self.test)

        if not context.session.is_successful(ReportLocation.in_test(self.test)):
            raise TaskFailure("test '%s' failed" % self.test.path)

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.test.path)


def build_test_task(test, suite_scheduled_fixtures, dependency):
    return TestTask(test, suite_scheduled_fixtures, dependency)


def build_suite_tasks(
        suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task,
        parent_suite_beginning_task=None, force_disabled=False):
    ###
    # Build suite beginning task
    ###
    suite_beginning_task = build_suite_beginning_task(
        suite, list((filter(bool, (test_session_setup_task, parent_suite_beginning_task))))
    )

    ###
    # Build suite setup task (if any)
    ###
    suite_scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_suite(
        suite, session_scheduled_fixtures, force_disabled
    )
    suite_setup_task = build_suite_initialization_task(
        suite, suite_scheduled_fixtures, [suite_beginning_task], force_disabled
    )

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
                sub_suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task, suite_beginning_task,
                force_disabled
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

    def get_on_success_dependencies(self):
        return self._dependencies

    def run(self, context):
        context.session.start_suite(self.suite)

    def skip(self, context, _):
        self.run(context)

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

    def get_on_success_dependencies(self):
        return self._dependencies

    def run(self, context):
        if any(setup for setup, _ in self.setup_teardown_funcs):
            # before actual initialization
            context.session.start_suite_setup(self.suite)
            context.session.set_step("Setup suite")
            # actual initialization
            self.teardown_funcs = context.run_setup_funcs(
                self.setup_teardown_funcs, ReportLocation.in_suite_setup(self.suite)
            )
            # after actual initialization
            context.session.end_suite_setup(self.suite)
            if not context.session.is_successful(ReportLocation.in_suite_setup(self.suite)):
                raise TaskFailure("suite '%s' setup failed" % self.suite.path)
        else:
            self.teardown_funcs = [teardown for _, teardown in self.setup_teardown_funcs if teardown]

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


def build_suite_initialization_task(suite, scheduled_fixtures, dependencies, force_disabled):
    if not suite.has_enabled_tests() and not force_disabled:
        return None

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

    def get_on_success_dependencies(self):
        return self._dependencies

    def run(self, context):
        context.session.end_suite(self.suite)

    def skip(self, context, _):
        self.run(context)

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

    def get_on_completion_dependencies(self):
        return self._dependencies

    def run(self, context):
        if any(self.suite_setup_task.teardown_funcs):
            # before actual teardown
            context.session.start_suite_teardown(self.suite)
            context.session.set_step("Teardown suite")
            # actual teardown
            context.run_teardown_funcs(self.suite_setup_task.teardown_funcs)
            # after actual teardown
            context.session.end_suite_teardown(self.suite)

    def skip(self, context, _):
        self.run(context)

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.suite.path)


def build_suite_teardown_task(suite, suite_setup_task, dependencies):
    return SuiteTeardownTask(suite, suite_setup_task, dependencies) if suite_setup_task else None


class TestSessionSetupTask(BaseTask):
    def __init__(self, scheduled_fixtures):
        BaseTask.__init__(self)
        self.scheduled_fixtures = scheduled_fixtures
        self.teardown_funcs = []

    def run(self, context):
        setup_teardown_funcs = self.scheduled_fixtures.get_setup_teardown_pairs()

        if any(setup for setup, _ in setup_teardown_funcs):
            # before actual setup
            context.session.start_test_session_setup()
            context.session.set_step("Setup test session")
            # actual setup
            self.teardown_funcs = context.run_setup_funcs(setup_teardown_funcs, ReportLocation.in_test_session_setup())
            # after actual setup
            context.session.end_test_session_setup()
            if not context.session.is_successful(ReportLocation.in_test_session_setup()):
                raise TaskFailure("test session setup failed")
        else:
            self.teardown_funcs = [teardown for _, teardown in setup_teardown_funcs if teardown]


def build_test_session_setup_task(scheduled_fixtures):
    return TestSessionSetupTask(scheduled_fixtures) if not scheduled_fixtures.is_empty() else None


class TestSessionTeardownTask(BaseTask):
    def __init__(self, test_session_setup_task, dependencies):
        BaseTask.__init__(self)
        self.test_session_setup_task = test_session_setup_task
        self._dependencies = dependencies

    def get_on_completion_dependencies(self):
        return self._dependencies

    def run(self, context):
        if any(self.test_session_setup_task.teardown_funcs):
            # before actual teardown
            context.session.start_test_session_teardown()
            context.session.set_step("Teardown test session")
            # actual teardown
            context.run_teardown_funcs(self.test_session_setup_task.teardown_funcs)
            # after actual teardown
            context.session.end_test_session_teardown()

    def skip(self, context, _):
        self.run(context)


def build_test_session_teardown_task(test_session_setup_task, dependencies):
    return TestSessionTeardownTask(test_session_setup_task, dependencies) if test_session_setup_task else None


def lookup_test_task(tasks, test_path):
    try:
        return next(task for task in tasks if isinstance(task, TestTask) and task.test.path == test_path)
    except StopIteration:
        raise LookupError("Cannot find test '%s' in tasks" % test_path)


def build_tasks(suites, fixture_registry, session_scheduled_fixtures, force_disabled):
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
            build_suite_tasks(
                suite, fixture_registry, session_scheduled_fixtures, test_session_setup_task,
                force_disabled=force_disabled
            )
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
    # Get all effective tasks (task != None)
    ###
    task_iter = itertools.chain((test_session_setup_task,), suite_tasks, (test_session_teardown_task,))
    tasks = list(filter(bool, task_iter))

    ###
    # Add extra dependencies in tasks for tests that depend on other tests
    ###
    for test in flatten_tests(suites):
        if not test.dependencies:
            continue
        test_task = lookup_test_task(tasks, test.path)
        for dep_test_path in test.dependencies:
            try:
                dep_test = lookup_test_task(tasks, dep_test_path)
            except LookupError:
                raise UserError(
                    "Cannot find dependency test '%s' for '%s', "
                    "either the test does not exist or is not going to be run" % (dep_test_path, test.path)
                )
            test_task.dependencies.append(dep_test)

    ###
    # Return tasks
    ###
    return tasks


def _run_suites(suites, fixture_registry, pre_run_scheduled_fixtures, session,
                force_disabled=False, stop_on_failure=False, nb_threads=1):
    # build tasks and run context
    session_scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_session(
        suites, pre_run_scheduled_fixtures, force_disabled
    )
    tasks = build_tasks(suites, fixture_registry, session_scheduled_fixtures, force_disabled)
    context = RunContext(session, fixture_registry, force_disabled, stop_on_failure)

    with session.event_manager.handle_events():
        session.start_test_session()
        run_tasks(tasks, context, nb_threads)
        session.end_test_session()

    exception, serialized_exception = session.event_manager.get_pending_failure()
    if exception:
        raise exception.__class__(serialized_exception)


def run_suites(suites, fixture_registry, session, force_disabled=False, stop_on_failure=False, nb_threads=1):
    fixture_teardowns = []

    # setup of 'pre_run' fixtures
    errors = []
    scheduled_fixtures = fixture_registry.get_fixtures_scheduled_for_pre_run(suites, force_disabled)
    initialize_fixture_cache(scheduled_fixtures)
    for setup, teardown in scheduled_fixtures.get_setup_teardown_pairs():
        try:
            setup()
        except UserError:
            raise
        except Exception:
            errors.append("Got the following exception when executing fixture (scope 'pre_run')%s" % (
                serialize_current_exception(show_stacktrace=True)
            ))
            break
        fixture_teardowns.append(teardown)

    if not errors:
        _run_suites(
            suites, fixture_registry, scheduled_fixtures, session,
            force_disabled=force_disabled, stop_on_failure=stop_on_failure, nb_threads=nb_threads
        )

    # teardown of 'pre_run' fixtures
    for teardown in fixture_teardowns:
        try:
            teardown()
        except UserError:
            raise
        except Exception:
            errors.append("Got the following exception on fixture teardown (scope 'pre_run')%s" % (
                serialize_current_exception(show_stacktrace=True)
            ))

    if errors:
        raise LemoncheesecakeException("\n".join(errors))
    else:
        return session.report.is_successful()
