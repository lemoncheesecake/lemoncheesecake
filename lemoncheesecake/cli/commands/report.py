from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, add_report_path_cli_arg, get_report_path
from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.backends.console import display_report
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter


class ReportCommand(Command):
    def get_name(self):
        return "report"

    def get_description(self):
        return "Display a report"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Show report")
        add_report_path_cli_arg(group)
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        display_report(
            load_report(report_path, auto_detect_reporting_backends()),
            make_report_filter(cli_args)
        )

        return 0
