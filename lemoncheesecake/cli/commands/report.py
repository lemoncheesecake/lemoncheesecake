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
        add_report_filter_cli_args(cli_parser)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)
        report = load_report(report_path, auto_detect_reporting_backends())
        filtr = make_report_filter(cli_args)

        if cli_args.short:
            print_report_as_test_run(report, filtr)
        else:
            print_report(report, filtr)

        return 0
