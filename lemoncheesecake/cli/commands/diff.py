from __future__ import print_function

from termcolor import colored
import colorama

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.reporting.console import test_status_to_color
from lemoncheesecake.reporting import load_report
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter, \
    filter_suites
from lemoncheesecake.testtree import flatten_tests, find_test
from lemoncheesecake.exceptions import CannotFindTreeNode, UserError

ORDERED_STATUSES = "failed", "skipped", "disabled", "passed"


class Diff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.status_changed = {}

    def is_empty(self):
        return len(self.added) + len(self.removed) + len(self.status_changed) == 0


def compute_diff(old_suites, new_suites):
    diff = Diff()

    new_tests = {test.path: test for test in flatten_tests(new_suites)}
    for old_test in flatten_tests(old_suites):
        # handle removed tests
        try:
            new_test = find_test(new_suites, old_test.path)
        except CannotFindTreeNode:
            diff.removed.append(old_test)
            continue

        # handle status-changed tests
        if new_test.status != old_test.status:
            if old_test.status not in diff.status_changed:
                diff.status_changed[old_test.status] = {}
            if new_test.status not in diff.status_changed[old_test.status]:
                diff.status_changed[old_test.status][new_test.status] = []
            diff.status_changed[old_test.status][new_test.status].append(new_test)

        del new_tests[new_test.path]

    # handle added tests
    diff.added.extend(new_tests.values())

    return diff


def display_diff_type(title, test_entries):
    if len(test_entries) == 0:
        return

    print("%s (%d):" % (colored(title, attrs=["bold"]), len(test_entries)))
    for test_entry in test_entries:
        print("- %s" % test_entry)
    print()


def render_test_with_status(test):
    return "%s (%s)" % (test.path, colored(test.status, test_status_to_color(test.status)))


def render_test_with_status_changed(test, old_status):
    return "%s (%s => %s)" % (
        test.path,
        colored(old_status, test_status_to_color(old_status)),
        colored(test.status, test_status_to_color(test.status))
    )


def flatten_test_status_changed(status_changed):
    for old_status in ORDERED_STATUSES:
        for new_status in ORDERED_STATUSES:
            for test in status_changed.get(old_status, {}).get(new_status, []):
                yield test, old_status


def display_diff(diff):
    if diff.is_empty():
        print("There is no difference between the two reports.")
    else:
        display_diff_type(
            "Added tests", [render_test_with_status(test) for test in diff.added]
        )
        display_diff_type(
            "Removed tests", [render_test_with_status(test) for test in diff.removed]
        )
        display_diff_type(
            "Status changed",
            [
                render_test_with_status_changed(test, old_status)
                    for test, old_status in flatten_test_status_changed(diff.status_changed)
            ]
        )


class DiffCommand(Command):
    def get_name(self):
        return "diff"

    def get_description(self):
        return "Display differences between two reports"

    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("old_report_path", help="Old report path")
        cli_parser.add_argument("new_report_path", help="New report path")
        add_report_filter_cli_args(cli_parser)

    def run_cmd(self, cli_args):
        colorama.init()

        reporting_backends = auto_detect_reporting_backends()

        old_report = load_report(cli_args.old_report_path, reporting_backends)
        new_report = load_report(cli_args.new_report_path, reporting_backends)
        filtr = make_report_filter(cli_args)

        old_suites = filter_suites(old_report.get_suites(), filtr)
        new_suites = filter_suites(new_report.get_suites(), filtr)

        if len(old_suites) == 0 and len(new_suites) == 0:
            raise UserError("The filter does not match any test on both reports")

        diff = compute_diff(old_suites, new_suites)
        display_diff(diff)

        return 0
