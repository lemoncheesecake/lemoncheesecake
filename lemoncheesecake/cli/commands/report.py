import os.path as osp

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.project import find_project_dir
from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.backends.console import display_report_suites
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter, filter_suites
from lemoncheesecake.exceptions import UserError

class ReportCommand(Command):
    def get_name(self):
        return "report"

    def get_description(self):
        return "Display a report"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Show report")
        group.add_argument("report_path", nargs='?', help="Report file name or directory")
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        if cli_args.report_path is None:
            project_dirname = find_project_dir()
            if project_dirname is None:
                raise UserError("Cannot find project")
            report_path = osp.join(project_dirname, DEFAULT_REPORT_DIR_NAME)
        else:
            report_path = cli_args.report_path

        report = load_report(report_path, auto_detect_reporting_backends())
        suites = filter_suites(report.get_suites(), make_report_filter(cli_args))

        display_report_suites(suites)

        return 0
