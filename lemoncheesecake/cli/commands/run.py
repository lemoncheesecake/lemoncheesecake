'''
Created on Dec 31, 2016

@author: nicolas
'''

import os

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import load_suites_from_project
from lemoncheesecake.exceptions import LemoncheesecakeException, ProgrammingError, UserError, \
    serialize_current_exception
from lemoncheesecake.filter import add_run_filter_cli_args, make_run_filter
from lemoncheesecake.fixture import FixtureRegistry, BuiltinFixture
from lemoncheesecake.project import find_project_file, load_project_from_file, load_project, DEFAULT_REPORTING_BACKENDS
from lemoncheesecake.reporting.backend import ReportingSessionBuilderMixin
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy
from lemoncheesecake.runner import initialize_event_manager, run_suites


def build_fixture_registry(project, cli_args):
    registry = FixtureRegistry()
    registry.add_fixture(BuiltinFixture("cli_args", lambda: cli_args))
    registry.add_fixture(BuiltinFixture("project_dir", lambda: project.dir))
    for fixture in project.load_fixtures():
        registry.add_fixture(fixture)
    registry.check_dependencies()
    return registry


def get_nb_threads(cli_args):
    if cli_args.threads is not None:
        return max(cli_args.threads, 1)
    elif "LCC_THREADS" in os.environ:
        try:
            return max(int(os.environ["LCC_THREADS"]), 1)
        except ValueError:
            raise LemoncheesecakeException(
                "Invalid value '%s' for $LCC_THREADS environment variable (expect integer)" % os.environ["LCC_THREADS"]
            )
    else:
        return 1


def get_report_saving_strategy(cli_args):
    saving_strategy_expression = cli_args.save_report or os.environ.get("LCC_SAVE_REPORT") or "at_each_failed_test"

    try:
        return make_report_saving_strategy(saving_strategy_expression)
    except ValueError:
        raise LemoncheesecakeException("Invalid expression '%s' for report saving strategy" % saving_strategy_expression)


class ReportSetupHandler(object):
    def __init__(self, project):
        self.project = project

    def __call__(self, event):
        title = self.project.build_report_title()
        if title:
            event.report.title = title

        for key, value in self.project.build_report_info():
            event.report.add_info(key, value)


def run_project(project, cli_args):
    nb_threads = get_nb_threads(cli_args)
    if nb_threads > 1 and not project.threaded:
        raise LemoncheesecakeException("Project does not support multi-threading")

    suites = load_suites_from_project(project, make_run_filter(cli_args))

    # Build fixture registry
    fixture_registry = build_fixture_registry(project, cli_args)
    fixture_registry.check_fixtures_in_suites(suites)

    # Get reporting backends
    reporting_backends = []
    for backend_name in cli_args.reporting:
        try:
            backend = project.reporting_backends[backend_name]
        except KeyError:
            raise LemoncheesecakeException("Unknown reporting backend '%s'" % backend_name)
        if not isinstance(backend, ReportingSessionBuilderMixin):
            raise LemoncheesecakeException("Reporting backend '%s' is not suitable for test run" % backend_name)
        reporting_backends.append(backend)

    # Get report save mode
    report_saving_strategy = get_report_saving_strategy(cli_args)

    # Create report dir
    if cli_args.report_dir:
        report_dir = cli_args.report_dir
        try:
            os.mkdir(report_dir)
        except Exception as e:
            return LemoncheesecakeException("Cannot create report directory: %s" % e)
    else:
        try:
            report_dir = project.create_report_dir()
        except UserError as e:
            raise e
        except Exception:
            raise LemoncheesecakeException(
                "Got an unexpected exception while creating report directory:%s" % \
                serialize_current_exception(show_stacktrace=True)
            )

    # Handle before run hook
    try:
        project.pre_run(cli_args, report_dir)
    except UserError as e:
        raise e
    except Exception:
        raise ProgrammingError(
            "Got an unexpected exception while running the pre-session hook:%s" % \
            serialize_current_exception(show_stacktrace=True)
        )

    # Initialize event manager
    event_manager = initialize_event_manager(
        suites, reporting_backends, report_dir, report_saving_strategy, nb_threads
    )
    event_manager.subscribe_to_event("test_session_start", ReportSetupHandler(project))

    # Run tests
    is_successful = run_suites(
        suites, fixture_registry, event_manager,
        force_disabled=cli_args.force_disabled, stop_on_failure=cli_args.stop_on_failure,
        nb_threads=nb_threads
    )

    # Handle after run hook
    try:
        project.post_run(cli_args, report_dir)
    except UserError as e:
        raise e
    except Exception:
        raise ProgrammingError(
            "Got an unexpected exception while running the post-session hook:%s" % \
            serialize_current_exception(show_stacktrace=True)
        )

    if cli_args.exit_error_on_failure:
        return 0 if is_successful else 1
    else:
        return 0


class RunCommand(Command):
    def get_name(self):
        return "run"

    def get_description(self):
        return "Run the tests"

    def add_cli_args(self, cli_parser):
        project_file = find_project_file()
        if project_file:
            project = load_project_from_file(project_file)
            default_reporting_backend_names = project.default_reporting_backend_names
        else:
            project = None
            default_reporting_backend_names = DEFAULT_REPORTING_BACKENDS

        add_run_filter_cli_args(cli_parser)

        test_execution_group = cli_parser.add_argument_group("Test execution")
        test_execution_group.add_argument(
            "--force-disabled", action="store_true",
            help="Force the run of disabled tests"
        )
        test_execution_group.add_argument(
            "--exit-error-on-failure", action="store_true",
            help="Exit with non-zero code if there is at least one non-passed test"
        )
        test_execution_group.add_argument(
            "--stop-on-failure", action="store_true",
            help="Stop tests execution on the first non-passed test"
        )
        test_execution_group.add_argument(
            "--threads", type=int, default=None,
            help="Number of threads used to run tests (default: $LCC_THREADS or 1)"
        )

        reporting_group = cli_parser.add_argument_group("Reporting")
        reporting_group.add_argument(
            "--report-dir", "-r", required=False,
            help="Directory where report data will be stored"
        )
        reporting_group.add_argument(
            "--reporting", nargs="+", default=default_reporting_backend_names,
            help="The list of reporting backends to use (default: %s)" % ", ".join(default_reporting_backend_names)
        )
        reporting_group.add_argument(
            "--save-report", required=False,
            help="At what frequency the reporting backends such as json or xml must save reporting data to disk. "
                 "(default: $LCC_SAVE_REPORT_AT or at_each_failed_test, possible values are: "
                 "at_end_of_tests, at_each_suite, at_each_test, at_each_failed_test, at_each_event, every_${N}s)"
        )

        if project:
            cli_group = cli_parser.add_argument_group("Project custom arguments")
            project.add_cli_args(cli_group)

    def run_cmd(self, cli_args):
        return run_project(load_project(), cli_args)
