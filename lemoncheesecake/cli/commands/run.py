'''
Created on Dec 31, 2016

@author: nicolas
'''

import os

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import load_suites_from_project
from lemoncheesecake.exceptions import LemoncheesecakeException, ProjectNotFound, UserError, serialize_current_exception
from lemoncheesecake.filter import add_test_filter_cli_args, make_test_filter
from lemoncheesecake.project import load_project, run_project, DEFAULT_REPORTING_BACKENDS
from lemoncheesecake.reporting.backend import get_reporting_backend_names as do_get_reporting_backend_names, \
    parse_reporting_backend_names_expression, get_reporting_backends_for_test_run
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy, DEFAULT_REPORT_SAVING_STRATEGY


def get_nb_threads(cli_args, project):
    if cli_args.threads is not None:
        nb_threads = max(cli_args.threads, 1)
    elif "LCC_THREADS" in os.environ:
        try:
            nb_threads = max(int(os.environ["LCC_THREADS"]), 1)
        except ValueError:
            raise LemoncheesecakeException(
                "Invalid value '%s' for $LCC_THREADS environment variable (expect integer)" % os.environ["LCC_THREADS"]
            )
    else:
        nb_threads = 1

    if nb_threads > 1 and not project.threaded:
        raise LemoncheesecakeException("Project does not support multi-threading")

    return nb_threads


def get_report_saving_strategy(cli_args):
    saving_strategy_expression = cli_args.save_report or \
        os.environ.get("LCC_SAVE_REPORT") or DEFAULT_REPORT_SAVING_STRATEGY
    try:
        return make_report_saving_strategy(saving_strategy_expression)
    except ValueError as excp:
        raise LemoncheesecakeException(str(excp))


def get_reporting_backend_names(cli_args, project):
    if cli_args.reporting:
        try:
            return do_get_reporting_backend_names(
                project.default_reporting_backend_names, cli_args.reporting
            )
        except ValueError as e:
            raise LemoncheesecakeException("Invalid --reporting argument: %s" % e)
    elif "LCC_REPORTING" in os.environ:
        try:
            return do_get_reporting_backend_names(
                project.default_reporting_backend_names,
                parse_reporting_backend_names_expression(os.environ["LCC_REPORTING"])
            )
        except ValueError as e:
            raise LemoncheesecakeException("Invalid $LCC_REPORTING: %s" % e)
    else:
        return project.default_reporting_backend_names


def create_report_dir(cli_args, project):
    report_dir = cli_args.report_dir or os.environ.get("LCC_REPORT_DIR")
    if report_dir:
        try:
            os.mkdir(report_dir)
        except OSError as e:
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

    return report_dir


def run_suites_from_project(project, cli_args):
    # Load suites
    suites = load_suites_from_project(project, make_test_filter(cli_args))

    # Get reporting backends
    reporting_backend_names = get_reporting_backend_names(cli_args, project)
    reporting_backends = get_reporting_backends_for_test_run(project.reporting_backends, reporting_backend_names)

    # Get report save mode
    report_saving_strategy = get_report_saving_strategy(cli_args)

    # Create report dir
    report_dir = create_report_dir(cli_args, project)

    # Get number of threads
    nb_threads = get_nb_threads(cli_args, project)

    # Run tests
    report = run_project(
        project, suites, cli_args, reporting_backends, report_dir, report_saving_strategy,
        cli_args.force_disabled, cli_args.stop_on_failure, nb_threads
    )

    # Return exit code
    if cli_args.exit_error_on_failure:
        return 0 if report.is_successful() else 1
    else:
        return 0


class RunCommand(Command):
    def get_name(self):
        return "run"

    def get_description(self):
        return "Run the tests"

    def add_cli_args(self, cli_parser):
        try:
            project = load_project()
            default_reporting_backend_names = project.default_reporting_backend_names
        except ProjectNotFound:
            project = None
            default_reporting_backend_names = DEFAULT_REPORTING_BACKENDS

        add_test_filter_cli_args(cli_parser)

        project_group = cli_parser.add_argument_group("Project")
        project_group.add_argument(
            "--project", "-p", required=False,
            help="Project path (default: $LCC_PROJECT or lookup for a project in the directory hierarchy)"
        )

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
            help="Directory where report data will be stored (default: $LCC_REPORT_DIR or 'report' depending on "
                 "the project configuration)"
        )
        reporting_group.add_argument(
            "--reporting", nargs="+", default=[],
            help="The list of reporting backends to use (default: %s)" % ", ".join(default_reporting_backend_names)
        )
        reporting_group.add_argument(
            "--save-report", required=False,
            help="At what frequency the reporting backends such as json or xml must save reporting data to disk. "
                 "(default: $LCC_SAVE_REPORT or at_each_failed_test, possible values are: "
                 "at_end_of_tests, at_each_suite, at_each_test, at_each_failed_test, at_each_log, every_${N}s)"
        )

        if project:
            cli_group = cli_parser.add_argument_group("Project custom arguments")
            project.add_cli_args(cli_group)

    def run_cmd(self, cli_args):
        return run_suites_from_project(load_project(cli_args.project), cli_args)
