from __future__ import print_function

from terminaltables import AsciiTable
from termcolor import colored
import six

from lemoncheesecake.helpers.text import wrap_text
from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.helpers import terminalsize
from lemoncheesecake.filter import ResultFilter
from lemoncheesecake.reporting import Log, Check, Url, Attachment, TestResult


def test_status_to_color(status):
    return {
        "passed": "green",
        "failed": "red",
        "disabled": "cyan",
        "in_progress": "cyan",
        None: "cyan"  # None means test is in progress
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
    def __init__(self, max_width, explicit=False, highlight=None, show_debug_logs=False):
        self.max_width = max_width
        self.explicit = explicit
        self.highlight = highlight
        self.show_debug_logs = show_debug_logs
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

    def render_highlighted(self, content):
        if not self.highlight or not content:
            return content

        return self.highlight.sub(
            lambda m: colored(m.group(0), color="yellow", attrs=["bold", "underline"]), content
        )

    def render_step_log(self, log):
        if isinstance(log, Log):
            if log.level == "debug" and not self.show_debug_logs:
                return None
            else:
                return [
                    colored(log.level.upper(), color=log_level_to_color(log.level), attrs=["bold"]),
                    self.render_highlighted(self.wrap_description_col(log.message))
                ]
        if isinstance(log, Check):
            return [
                self.render_check_outcome(log.is_successful),
                self.render_highlighted(self.wrap_description_col(log.description)),
                self.render_highlighted(self.wrap_details_col(log.details))
            ]
        if isinstance(log, Url):
            if log.description == log.url:
                description = log.url
            else:
                description = "%s (%s)" % (log.url, log.description)
            return [
                colored("URL", color="cyan", attrs=["bold"]),
                self.render_highlighted(self.wrap_description_col(description))
            ]
        if isinstance(log, Attachment):
            return [
                colored("ATTACH", color="cyan", attrs=["bold"]),
                self.render_highlighted(self.wrap_description_col(log.description)),
                self.render_highlighted(log.filename)
            ]

        raise ValueError("Unknown step log class '%s'" % log.__class__.__name__)

    def render_steps(self, steps):
        rows = []
        for step in steps:
            step_log_rows = list(filter(bool, map(self.render_step_log, step.get_logs())))
            if step_log_rows:
                rows.append([
                    "",
                    colored(
                        self.render_highlighted(self.wrap_description_col(step.description)),
                        color=outcome_to_color(step.is_successful()),
                        attrs=["bold"]
                    ),
                    colored(humanize_duration(step.duration, show_milliseconds=True), attrs=["bold"])
                        if step.duration is not None else "-"
                ])
                rows.extend(step_log_rows)

        if not rows:
            return None

        table = AsciiTable(rows)
        table.inner_heading_row_border = False
        table.justify_columns[0] = "center"
        table.inner_row_border = True

        return table.table

    def render_chunk(self, description, short_description, status, steps):
        if status is None:
            status = "in_progress"

        if steps:
            details = self.render_steps(steps) or "n/a"
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

        return self.render_chunk(test.description, short_description, test.status, test.get_steps())

    def render_result(self, result):
        if result.type == "suite_setup":
            description = "- SUITE SETUP - %s" % result.parent_suite.description
            short_description = result.parent_suite.path
        elif result.type == "suite_teardown":
            description = "- SUITE TEARDOWN - %s" % result.parent_suite.description
            short_description = result.parent_suite.path
        elif result.type == "test_session_setup":
            description = "- TEST SESSION SETUP -"
            short_description = None
        elif result.type == "test_session_teardown":
            description = "- TEST SESSION TEARDOWN -"
            short_description = None
        else:
            raise ValueError("Unknown result type '%s'" % result.type)

        return self.render_chunk(description, short_description, result.status, result.get_steps())

    def render_results(self, results):
        for result in results:
            if isinstance(result, TestResult):
                yield self.render_test(result)
            else:
                yield self.render_result(result)
            yield ""


def _print_chunks(chunks):
    for chunk in chunks:
        print(chunk if six.PY3 else chunk.encode("utf8"))


def print_report(report, result_filter=None, max_width=None, show_debug_logs=False, explicit=False):
    ###
    # Setup terminal
    ###
    if not max_width:
        max_width, _ = terminalsize.get_terminal_size()

    ###
    # Get a generator over data to be printed on the console
    ###
    renderer = Renderer(
        max_width=max_width, show_debug_logs=show_debug_logs, explicit=explicit,
        highlight=result_filter.grep if isinstance(result_filter, ResultFilter) else None
    )
    if not result_filter:
        if report.nb_tests == 0:
            print("No tests found in report")
            return
        chunks = renderer.render_results(report.all_results())
    else:
        results = list(filter(result_filter, report.all_results()))
        if not results:
            print("The filter does not match anything in the report")
            return
        chunks = renderer.render_results(results)

    ###
    # Do the actual job
    ###
    _print_chunks(chunks)
