from __future__ import print_function

from functools import partial

from terminaltables import AsciiTable
import colorama
from termcolor import colored
import six

from lemoncheesecake.helpers.text import wrap_text
from lemoncheesecake.helpers import terminalsize
from lemoncheesecake.reporting import LogData, CheckData, UrlData, AttachmentData
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.filter import filter_suites


def test_status_to_color(status):
    return {
        "passed": "green",
        "failed": "red",
        "disabled": "cyan",
    }.get(status, "yellow")


def log_level_to_color(level):
    return {
        "debug": "cyan",
        "info": "cyan",
        "warn": "yellow",
        "error": "red"
    }.get(level, "cyan")


def outcome_to_color(outcome):
    return "green" if outcome else "red"


class Renderer(object):
    def __init__(self, max_width):
        self.max_width = max_width
        # "15" is an approximation of the maximal overhead of table border, padding, and table first cell
        self._table_overhead = 15

    def wrap_description_col(self, description):
        return wrap_text(description, int((self.max_width - self._table_overhead) * 0.75))

    def wrap_details_col(self, details):
        return wrap_text(details, int((self.max_width - self._table_overhead) * 0.25))

    def render_steps(self, steps):
        rows = []
        for step in steps:
            rows.append(["", colored(self.wrap_description_col(step.description), attrs=["bold"])])
            for entry in step.entries:
                if isinstance(entry, LogData):
                    rows.append([
                        colored(entry.level.upper(), color=log_level_to_color(entry.level), attrs=["bold"]),
                        self.wrap_description_col(entry.message)
                    ])
                if isinstance(entry, CheckData):
                    rows.append([
                        colored("CHECK", color=outcome_to_color(entry.outcome), attrs=["bold"]),
                        self.wrap_description_col(entry.description),
                        self.wrap_details_col(entry.details)
                    ])
                if isinstance(entry, UrlData):
                    rows.append([
                        colored("URL", color="cyan", attrs=["bold"]),
                        self.wrap_description_col("%s (%s)" % (entry.url, entry.description))
                    ])
                if isinstance(entry, AttachmentData):
                    rows.append([
                        colored("ATTACH", color="cyan", attrs=["bold"]),
                        self.wrap_description_col(entry.description),
                        "IMAGE" if entry.as_image else ""
                    ])

        table = AsciiTable(rows)
        table.inner_heading_row_border = False
        table.justify_columns[0] = "center"
        table.inner_row_border = True

        return table.table

    def render_result(self, description, short_description, status, steps):
        if steps:
            details = self.render_steps(steps)
        else:
            details = "n/a"

        parts = [colored(description, color=test_status_to_color(status), attrs=["bold"])]
        if short_description:
            parts.append(colored("(%s)" % short_description, attrs=["bold"]))
        parts.append(details)

        return "\n".join(parts)

    def render_test(self, test):
        return self.render_result(test.description, test.path, test.status, test.steps)

    def render_tests(self, suites):
        for test in flatten_tests(suites):
            yield self.render_test(test)

    def render_report(self, report):
        if report.test_session_setup:
            yield self.render_result(
                "- TEST SESSION SETUP -", None,
                report.test_session_setup.status, report.test_session_setup.steps
            )

        for suite in report.all_suites():
            if suite.suite_setup:
                yield self.render_result(
                    "- SUITE SETUP - %s" % suite.description, suite.path,
                    suite.suite_setup.status, suite.suite_setup.steps
                )

            for test in suite.get_tests():
                yield self.render_test(test)

            if suite.suite_teardown:
                yield self.render_result(
                    "- SUITE TEARDOWN - %s" % suite.description, suite.path,
                    suite.suite_teardown.status, suite.suite_teardown.steps
                )

        if report.test_session_teardown:
            yield self.render_result(
                "- TEST SESSION TEARDOWN -", None,
                report.test_session_teardown.status, report.test_session_teardown.steps
            )


def _print_results(results):
    for result in results:
        print(result if six.PY3 else result.encode("utf8"))
        print()


def print_report(report, filtr=None):
    ###
    # Setup terminal
    ###
    colorama.init()
    terminal_width, _ = terminalsize.get_terminal_size()

    ###
    # Get a generator over data to be printed on the console
    ###
    renderer = Renderer(terminal_width)
    if not filtr or filtr.is_empty():
        if report.nb_tests == 0:
            print("No tests found in report")
            return
        results = renderer.render_report(report)
    else:
        suites = filter_suites(report.get_suites(), filtr)
        if not suites:
            print("The filter does not match any test in the report")
            return
        results = renderer.render_tests(suites)

    ###
    # Do the actual job
    ###
    _print_results(results)
