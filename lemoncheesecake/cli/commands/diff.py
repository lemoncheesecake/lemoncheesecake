from __future__ import print_function

from termcolor import colored

from lemoncheesecake.utils import get_status_color
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.reporting import load_report
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter, \
    filter_suites, ReportFilter
from lemoncheesecake.testtree import flatten_tests, find_test
from lemoncheesecake.exceptions import CannotFindTreeNode, UserError


class Diff:
    def __init__(self):
        self.added = []
        self.removed = []
        self.passed = []
        self.non_passed = []

    def is_empty(self):
        return len(self.added + self.removed + self.passed + self.non_passed) == 0


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
            if new_test.status == "passed":
                diff.passed.append(new_test)
            else:
                diff.non_passed.append(new_test)

        del new_tests[new_test.path]

    # handle added tests
    diff.added.extend(new_tests.values())

    return diff


def display_diff_type(title, tests, hide_status=False):
    if len(tests) == 0:
        return

    print("%s (%d):" % (title, len(tests)))
    for test in tests:
        line = "- %s" % test.path
        if not hide_status:
            line += " (%s)" % colored(test.status, get_status_color(test.status))
        print(line)
    print()


def display_diff(diff):
    if diff.is_empty():
        print("There is no difference between the two reports.")
    else:
        display_diff_type(
            colored("Added tests", attrs=["bold"]), diff.added
        )
        display_diff_type(
            colored("Removed tests", "grey", attrs=["bold"]), diff.removed
        )
        display_diff_type(
            colored("Tests that switched to passed", get_status_color("passed"), attrs=["bold"]), diff.passed,
            hide_status=True
        )
        display_diff_type(
            colored("Tests that switched to non-passed", get_status_color("failed"), attrs=["bold"]), diff.non_passed
        )


class DiffCommand(Command):
    def get_name(self):
        return "diff"

    def get_description(self):
        return "Display differences between two reports"

    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("old_report_path", help="Old report path")
        cli_parser.add_argument("new_report_path", help="New report path")
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        reporting_backends = auto_detect_reporting_backends()

        old_report = load_report(cli_args.old_report_path, reporting_backends)
        new_report = load_report(cli_args.new_report_path, reporting_backends)
        filtr = make_report_filter(cli_args)

        old_suites = filter_suites(old_report.suites, filtr)
        new_suites = filter_suites(new_report.suites, filtr)

        if len(old_suites) == 0 and len(new_suites) == 0:
            raise UserError("The filter does not match any test on both reports")

        diff = compute_diff(old_suites, new_suites)
        display_diff(diff)

        return 0
