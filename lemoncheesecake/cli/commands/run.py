'''
Created on Dec 31, 2016

@author: nicolas
'''

import os
from collections import OrderedDict

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import get_suites_from_project
from lemoncheesecake.exceptions import LemonCheesecakeException, ProgrammingError, UserError, \
    serialize_current_exception
from lemoncheesecake.filter import add_run_filter_cli_args
from lemoncheesecake.fixtures import FixtureRegistry, BuiltinFixture
from lemoncheesecake.project import find_project_file, load_project_from_file, load_project
from lemoncheesecake.reporting import filter_reporting_backends_by_capabilities, CAPABILITY_REPORTING_SESSION
from lemoncheesecake.reporting.backend import FileReportBackend, SAVE_AT_EACH_EVENT, SAVE_AT_EACH_FAILED_TEST, SAVE_AT_EACH_SUITE, \
    SAVE_AT_EACH_TEST, SAVE_AT_END_OF_TESTS
from lemoncheesecake.runner import run_suites
from lemoncheesecake import events

SAVE_REPORT_AT_VALUES = OrderedDict((
    ("end_of_tests", SAVE_AT_END_OF_TESTS),
    ("each_suite", SAVE_AT_EACH_SUITE),
    ("each_test", SAVE_AT_EACH_TEST),
    ("each_failed_test", SAVE_AT_EACH_FAILED_TEST),
    ("each_event", SAVE_AT_EACH_EVENT)
))


def build_fixture_registry(project, cli_args):
    registry = FixtureRegistry()
    registry.add_fixture(BuiltinFixture("cli_args", lambda: cli_args))
    registry.add_fixture(BuiltinFixture("project_dir", lambda: project.get_project_dir()))
    for fixture in project.get_fixtures():
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
            raise LemonCheesecakeException(
                "Invalid value '%s' for $LCC_THREADS environment variable (expect integer)" % os.environ["LCC_THREADS"]
            )
    else:
        return 1


def get_report_save_mode(cli_args):
    if cli_args.save_report_at:
        return SAVE_REPORT_AT_VALUES[cli_args.save_report_at]
    elif "LCC_SAVE_REPORT_AT" in os.environ:
        try:
            return SAVE_REPORT_AT_VALUES[os.environ["LCC_SAVE_REPORT_AT"]]
        except KeyError:
            raise LemonCheesecakeException(
                "Invalid value '%s' for $LCC_SAVE_REPORT_AT environment variable; accepted values are: %s" % (
                    os.environ["LCC_SAVE_REPORT_AT"], ", ".join(SAVE_REPORT_AT_VALUES.keys())
                )
            )
    else:
        return SAVE_AT_EACH_FAILED_TEST


def run_project(project, cli_args):
    nb_threads = get_nb_threads(cli_args)
    if nb_threads > 1 and not project.is_threaded():
        raise LemonCheesecakeException("Project does not support multi-threading")

    suites = get_suites_from_project(project, cli_args)
    events.add_listener(project)

    # Build fixture registry
    fixture_registry = build_fixture_registry(project, cli_args)
    fixture_registry.check_fixtures_in_suites(suites)

    # Set active reporting backends
    available_reporting_backends = {
        backend.name: backend for backend in
        filter_reporting_backends_by_capabilities(
            project.get_all_reporting_backends(), CAPABILITY_REPORTING_SESSION
        )
    }
    active_reporting_backends = set()
    for backend_name in cli_args.reporting + cli_args.enable_reporting:
        try:
            active_reporting_backends.add(available_reporting_backends[backend_name])
        except KeyError:
            raise LemonCheesecakeException("Unknown reporting backend '%s'" % backend_name)
    for backend_name in cli_args.disable_reporting:
        try:
            active_reporting_backends.discard(available_reporting_backends[backend_name])
        except KeyError:
            raise LemonCheesecakeException("Unknown reporting backend '%s'" % backend_name)

    # Set report save mode (when relevant)
    save_mode = get_report_save_mode(cli_args)
    for reporting_backend in active_reporting_backends:
        if isinstance(reporting_backend, FileReportBackend):
            reporting_backend.save_mode = save_mode

    # Create report dir
    if cli_args.report_dir:
        report_dir = cli_args.report_dir
        try:
            os.mkdir(report_dir)
        except Exception as e:
            return LemonCheesecakeException("Cannot create report directory: %s" % e)
    else:
        try:
            report_dir = project.create_report_dir()
        except UserError as e:
            raise e
        except Exception:
            raise LemonCheesecakeException(
                "Got an unexpected exception while creating report directory:%s" % \
                serialize_current_exception(show_stacktrace=True)
            )

    # Handle before run hook
    try:
        project.run_pre_session_hook(cli_args, report_dir)
    except UserError as e:
        raise e
    except Exception:
        raise ProgrammingError(
            "Got an unexpected exception while running the pre-session hook:%s" % \
            serialize_current_exception(show_stacktrace=True)
        )

    # Run tests
    is_successful = run_suites(
        suites, fixture_registry, active_reporting_backends, report_dir,
        force_disabled=cli_args.force_disabled, stop_on_failure=cli_args.stop_on_failure,
        nb_threads=nb_threads
    )

    # Handle after run hook
    try:
        project.run_post_session_hook(cli_args, report_dir)
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
        project = None
        default_reporting_backend_names = []
        if project_file:
            project = load_project_from_file(project_file)
            default_reporting_backend_names = [backend.name for backend in project.get_default_reporting_backends_for_test_run()]

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
            help="The list of reporting backends to use"
        )
        reporting_group.add_argument(
            "--enable-reporting", nargs="+", default=[],
            help="The list of reporting backends to add (to base backends)"
        )
        reporting_group.add_argument(
            "--disable-reporting", nargs="+", default=[],
            help="The list of reporting backends to remove (from base backends)"
        )
        reporting_group.add_argument(
            "--save-report-at", default=None, choices=SAVE_REPORT_AT_VALUES.keys(),
            help="At what frequency the reporting backends such as json or xml must save reporting data to disk. "
                 "(default: $LCC_SAVE_REPORT_AT or each_failed_test)"
        )

        if project:
            project.add_custom_args_to_run_cli(cli_parser)

    def run_cmd(self, cli_args):
        return run_project(load_project(), cli_args)
