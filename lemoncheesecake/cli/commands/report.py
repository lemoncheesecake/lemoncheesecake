import sys

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, add_report_path_cli_arg, get_report_path
from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.backends.console import print_report_as_test_run
from lemoncheesecake.reporting.console import print_report
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter


class ReportCommand(Command):
    def get_name(self):
        return "report"

    def get_description(self):
        return "Display a report"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Display report")
        add_report_path_cli_arg(group)
        group.add_argument(
            "--short", "-s", action="store_true", required=False,
            help="Display report as lcc run display test results"
        )
        group.add_argument(
            "--explicit", "-e", action="store_true", required=False,
            help="Make all indicators 'explicit' (i.e not only relying on a color-code), "
                 "will be enforced is stdout is redirected"
        )
        group.add_argument(
            "--max-width", "-w", type=int, required=False,
            help="Set a max width for tables (default is current terminal width)"
        )

        add_report_filter_cli_args(cli_parser)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)
        report = load_report(report_path, auto_detect_reporting_backends())
        filtr = make_report_filter(cli_args)

        if cli_args.short:
            print_report_as_test_run(report, filtr)
        else:
            print_report(
                report, filtr=filtr, max_width=cli_args.max_width,
                explicit=cli_args.explicit or not sys.stdout.isatty()
            )

        return 0
