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


def _render_steps(steps, terminal_width):
    # "15" is an approximation of the maximal overhead of table border, padding, and table first cell
    wrap_description = partial(wrap_text, width=int((terminal_width - 15) * 0.75))
    wrap_details = partial(wrap_text, width=int((terminal_width - 15) * 0.25))

    rows = []
    for step in steps:
        rows.append(["", colored(wrap_description(step.description), attrs=["bold"])])
        for entry in step.entries:
            if isinstance(entry, LogData):
                rows.append([
                    colored(entry.level.upper(), color=log_level_to_color(entry.level), attrs=["bold"]),
                    wrap_description(entry.message)
                ])
            if isinstance(entry, CheckData):
                rows.append([
                    colored("CHECK", color=outcome_to_color(entry.outcome), attrs=["bold"]),
                    wrap_description(entry.description),
                    wrap_details(entry.details)
                ])
            if isinstance(entry, UrlData):
                rows.append([
                    colored("URL", color="cyan", attrs=["bold"]),
                    wrap_description("%s (%s)" % (entry.url, entry.description))
                ])
            if isinstance(entry, AttachmentData):
                rows.append([
                    colored("ATTACH", color="cyan", attrs=["bold"]),
                    wrap_description(entry.description),
                    "IMAGE" if entry.as_image else ""
                ])

    table = AsciiTable(rows)
    table.inner_heading_row_border = False
    table.justify_columns[0] = "center"
    table.inner_row_border = True

    return table.table


def _render_result(description, short_description, status, steps, terminal_width):
    if steps:
        details = _render_steps(steps, terminal_width)
    else:
        details = "n/a"

    parts = [colored(description, color=test_status_to_color(status), attrs=["bold"])]
    if short_description:
        parts.append(colored("(%s)" % short_description, attrs=["bold"]))
    parts.append(details)

    return "\n".join(parts)


def _render_test(test, terminal_width):
    return _render_result(
        test.description, test.path, test.status, test.steps, terminal_width
    )


def _render_tests(suites, terminal_width):
    for test in flatten_tests(suites):
        yield _render_test(test, terminal_width)


def _render_report(report, terminal_width):
    if report.test_session_setup:
        yield _render_result(
            "- TEST SESSION SETUP -", None,
            report.test_session_setup.status, report.test_session_setup.steps,
            terminal_width
        )

    for suite in report.all_suites():
        if suite.suite_setup:
            yield _render_result(
                "- SUITE SETUP - %s" % suite.description, suite.path,
                suite.suite_setup.status, suite.suite_setup.steps,
                terminal_width
            )

        for test in suite.get_tests():
            yield _render_test(test, terminal_width)

        if suite.suite_teardown:
            yield _render_result(
                "- SUITE TEARDOWN - %s" % suite.description, suite.path,
                suite.suite_teardown.status, suite.suite_teardown.steps,
                terminal_width
            )

    if report.test_session_teardown:
        yield _render_result(
            "- TEST SESSION TEARDOWN -", None,
            report.test_session_teardown.status, report.test_session_teardown.steps,
            terminal_width
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
    if not filtr or filtr.is_empty():
        if report.nb_tests == 0:
            print("No tests found in report")
            return
        results = _render_report(report, terminal_width)
    else:
        suites = filter_suites(report.get_suites(), filtr)
        if not suites:
            print("The filter does not match any test in the report")
            return
        results = _render_tests(suites, terminal_width)

    ###
    # Do the actual job
    ###
    _print_results(results)
