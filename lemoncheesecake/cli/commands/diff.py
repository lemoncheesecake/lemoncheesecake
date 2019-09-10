from __future__ import print_function

from collections import defaultdict

from termcolor import colored

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.reporting.console import test_status_to_color
from lemoncheesecake.reporting import load_report
from lemoncheesecake.filter import add_result_filter_cli_args, make_result_filter
from lemoncheesecake.exceptions import UserError

ORDERED_STATUSES = "failed", "skipped", "disabled", "passed"


class Diff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.status_changed = defaultdict(lambda: defaultdict(list))

    def is_empty(self):
        return not any((self.added, self.removed, self.status_changed))


def compute_diff(report_1_tests, report_2_tests):
    diff = Diff()

    report_2_tests = report_2_tests[:]  # make a copy as a list will be modified
    for report_1_test in report_1_tests:
        # handle removed tests
        try:
            report_2_test = next(test for test in report_2_tests if test.path == report_1_test.path)
        except StopIteration:
            diff.removed.append(report_1_test)
            continue

        # handle status-changed tests
        if report_2_test.status != report_1_test.status:
            diff.status_changed[report_1_test.status][report_2_test.status].append(report_2_test)

        report_2_tests.remove(report_2_test)

    # handle added tests
    diff.added.extend(report_2_tests)

    return diff


def display_diff_type(title, test_entries):
    if not test_entries:
        return

    print("%s (%d):" % (colored(title, attrs=["bold"]), len(test_entries)))
    for test_entry in test_entries:
        print("- %s" % test_entry)
    print()


def render_test_with_status(test):
    return "%s (%s)" % (test.path, colored(test.status, test_status_to_color(test.status)))


def render_test_with_status_changed(test, former_status):
    return "%s (%s => %s)" % (
        test.path,
        colored(former_status, test_status_to_color(former_status)),
        colored(test.status, test_status_to_color(test.status))
    )


def flatten_test_status_changed(status_changed):
    for former_status in ORDERED_STATUSES:
        for new_status in ORDERED_STATUSES:
            for test in status_changed[former_status][new_status]:
                yield test, former_status


def display_diff(diff):
    if diff.is_empty():
        print("There is no difference between the two reports.")
    else:
        display_diff_type(
            "Added tests", list(map(render_test_with_status, diff.added))
        )
        display_diff_type(
            "Removed tests", list(map(render_test_with_status, diff.removed))
        )
        display_diff_type(
            "Status changed",
            [
                render_test_with_status_changed(test, former_status)
                    for test, former_status in flatten_test_status_changed(diff.status_changed)
            ]
        )


class DiffCommand(Command):
    def get_name(self):
        return "diff"

    def get_description(self):
        return "Display differences between two reports"

    def add_cli_args(self, cli_parser):
        add_result_filter_cli_args(cli_parser)
        group = cli_parser.add_argument_group("Diff")
        group.add_argument("report_1_path", help="Report 1 path")
        group.add_argument("report_2_path", help="Report 2 path")

    def run_cmd(self, cli_args):
        reporting_backends = auto_detect_reporting_backends()

        report_1 = load_report(cli_args.report_1_path, reporting_backends)
        report_2 = load_report(cli_args.report_2_path, reporting_backends)
        test_filter = make_result_filter(cli_args)

        report_1_tests = list(filter(test_filter, report_1.all_tests()))
        report_2_tests = list(filter(test_filter, report_2.all_tests()))

        if len(report_1_tests) == 0 and len(report_2_tests) == 0:
            raise UserError("The filter does not match any test on both reports")

        diff = compute_diff(report_1_tests, report_2_tests)
        display_diff(diff)

        return 0
