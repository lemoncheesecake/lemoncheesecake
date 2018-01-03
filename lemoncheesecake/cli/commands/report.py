from __future__ import print_function

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.backends.console import display_report_suites
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter, filter_suites


class ReportCommand(Command):
    def get_name(self):
        return "report"

    def get_description(self):
        return "Display a report"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Show report")
        group.add_argument("report_path", help="Report file name or directory")
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        report = load_report(cli_args.report_path, auto_detect_reporting_backends())
        suites = filter_suites(report.get_suites(), make_report_filter(cli_args))

        display_report_suites(suites)

        return 0
