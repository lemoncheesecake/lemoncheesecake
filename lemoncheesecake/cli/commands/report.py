from __future__ import print_function

from lemoncheesecake.cli.command import Command
from lemoncheesecake.reporting import load_report
from lemoncheesecake.project import find_project_file, load_project_from_file
from lemoncheesecake.reporting.backends.console import display_report_suites
from lemoncheesecake.filter import add_report_filter_args_to_cli_parser, make_report_filter_from_cli_args, filter_suites
from lemoncheesecake.exceptions import ProjectError


class ReportCommand(Command):
    def get_name(self):
        return "report"

    def get_description(self):
        return "Display a report"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Show report")
        group.add_argument("report_path", help="Report file name or directory")
        add_report_filter_args_to_cli_parser(cli_parser)

    def run_cmd(self, cli_args):
        project_filename = find_project_file()
        if project_filename is not None:
            try:
                project = load_project_from_file(project_filename)
            except ProjectError:
                # project is optional when reading a report
                report_backends = None
            else:
                report_backends = project.get_all_reporting_backends()
        else:
            report_backends = None

        report = load_report(cli_args.report_path, report_backends)
        suites = filter_suites(report.get_suites(), make_report_filter_from_cli_args(cli_args))

        display_report_suites(suites)

        return 0
