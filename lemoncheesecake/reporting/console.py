from __future__ import print_function

from terminaltables import AsciiTable
import colorama
from termcolor import colored
import six

from lemoncheesecake.helpers.text import wrap_text
from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.helpers import terminalsize
from lemoncheesecake.reporting import Log, Check, Url, Attachment
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.filter import filter_suites


def test_status_to_color(status):
    return {
        "passed": "green",
        "failed": "red",
        "disabled": "cyan",
        "in_progress": "cyan"
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


def _serialize_metadata(tags, properties, links, disabled):
    parts = []

    if disabled:
        parts.append("DISABLED")
    parts.extend(tags)
    parts.extend("%s:%s" % (key, properties[key]) for key in sorted(properties))
    parts.extend(link_name or link_url for link_url, link_name in links)

    return ", ".join(parts)


def serialize_metadata(obj, hide_disabled=False):
    return _serialize_metadata(
        obj.tags, obj.properties, obj.links,
        disabled=not hide_disabled and getattr(obj, "disabled", False)
    )


def serialize_hierarchy_metadata(obj, hide_disabled=False):
    return _serialize_metadata(
        obj.hierarchy_tags, obj.hierarchy_properties, obj.hierarchy_links,
        disabled=not hide_disabled and (hasattr(obj, "is_disabled") and obj.is_disabled())
    )


class Renderer(object):
    def __init__(self, max_width, explicit=False):
        self.max_width = max_width
        self.explicit = explicit
        # "20" is an approximation of the maximal overhead of table border, padding, and table first cell
        self._table_overhead = 20

    def wrap_description_col(self, description):
        return wrap_text(description, int((self.max_width - self._table_overhead) * 0.75))

    def wrap_details_col(self, details):
        return wrap_text(details, int((self.max_width - self._table_overhead) * 0.25))

    def render_check_outcome(self, is_successful):
        if self.explicit:
            check_label = "CHECK %s" % ("OK" if is_successful else "KO")
        else:
            check_label = "CHECK"

        return colored(check_label, color=outcome_to_color(is_successful), attrs=["bold"])

    def render_steps(self, steps):
        rows = []
        for step in steps:
            rows.append([
                "",
                colored(
                    self.wrap_description_col(step.description),
                    color=outcome_to_color(step.is_successful()),
                    attrs=["bold"]
                ),
                colored(humanize_duration(step.duration, show_milliseconds=True), attrs=["bold"])
                    if step.duration is not None else "-"
            ])
            for entry in step.entries:
                if isinstance(entry, Log):
                    rows.append([
                        colored(entry.level.upper(), color=log_level_to_color(entry.level), attrs=["bold"]),
                        self.wrap_description_col(entry.message)
                    ])
                if isinstance(entry, Check):
                    rows.append([
                        self.render_check_outcome(entry.is_successful),
                        self.wrap_description_col(entry.description),
                        self.wrap_details_col(entry.details)
                    ])
                if isinstance(entry, Url):
                    rows.append([
                        colored("URL", color="cyan", attrs=["bold"]),
                        self.wrap_description_col("%s (%s)" % (entry.url, entry.description))
                    ])
                if isinstance(entry, Attachment):
                    rows.append([
                        colored("ATTACH", color="cyan", attrs=["bold"]),
                        self.wrap_description_col(entry.description),
                        entry.filename
                    ])

        table = AsciiTable(rows)
        table.inner_heading_row_border = False
        table.justify_columns[0] = "center"
        table.inner_row_border = True

        return table.table

    def render_result(self, description, short_description, status, steps):
        if status is None:
            status = "in_progress"

        if steps:
            details = self.render_steps(steps)
        else:
            details = "n/a"

        parts = [
            colored(
                "%s: %s" % (status.upper(), description) if self.explicit else description,
                color=test_status_to_color(status),
                attrs=["bold"]
            )
        ]
        if short_description:
            parts.append(colored("(%s)" % short_description, attrs=["bold"]))
        parts.append(details)

        return "\n".join(parts)

    def render_test(self, test):
        test_metadata = serialize_hierarchy_metadata(test, hide_disabled=True)
        if test_metadata:
            short_description = "%s - %s" % (test.path, test_metadata)
        else:
            short_description = test.path

        return self.render_result(test.description, short_description, test.status, test.steps)

    def render_tests(self, tests):
        for test in tests:
            yield self.render_test(test)
            yield ""

    def render_suite(self, suite):
        if suite.suite_setup:
            yield self.render_result(
                "- SUITE SETUP - %s" % suite.description, suite.path,
                suite.suite_setup.status, suite.suite_setup.steps
            )
            yield ""

        for test in suite.get_tests():
            yield self.render_test(test)
            yield ""

        if suite.suite_teardown:
            yield self.render_result(
                "- SUITE TEARDOWN - %s" % suite.description, suite.path,
                suite.suite_teardown.status, suite.suite_teardown.steps
            )
            yield ""

    def render_report(self, report):
        if report.test_session_setup:
            yield self.render_result(
                "- TEST SESSION SETUP -", None,
                report.test_session_setup.status, report.test_session_setup.steps
            )
            yield ""

        for suite in report.all_suites():
            for data in self.render_suite(suite):
                yield data

        if report.test_session_teardown:
            yield self.render_result(
                "- TEST SESSION TEARDOWN -", None,
                report.test_session_teardown.status, report.test_session_teardown.steps
            )
            yield ""


def _print_data(data_it):
    for data in data_it:
        print(data if six.PY3 else data.encode("utf8"))


def print_report(report, filtr=None, max_width=None, explicit=False):
    ###
    # Setup terminal
    ###
    colorama.init()
    if not max_width:
        max_width, _ = terminalsize.get_terminal_size()

    ###
    # Get a generator over data to be printed on the console
    ###
    renderer = Renderer(max_width=max_width, explicit=explicit)
    if not filtr:
        if report.nb_tests == 0:
            print("No tests found in report")
            return
        data = renderer.render_report(report)
    else:
        suites = filter_suites(report.get_suites(), filtr)
        if not suites:
            print("The filter does not match any test in the report")
            return
        data = renderer.render_tests(flatten_tests(suites))

    ###
    # Do the actual job
    ###
    _print_data(data)
