from functools import reduce

from lemoncheesecake.utils import humanize_duration
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, add_report_path_cli_arg, get_report_path
from lemoncheesecake.cli.display import print_table
from lemoncheesecake.reporting import load_report
from lemoncheesecake.filter import add_report_filter_cli_args, make_report_filter, filter_suites
from lemoncheesecake.testtree import flatten_tests, flatten_suites
from lemoncheesecake.reporting.report import flatten_steps


def get_tests_ordered_by_duration(tests):
    return sorted(tests, key=lambda test: test.duration, reverse=True)


def get_suites_ordered_by_duration(suites):
    return sorted(
        filter(lambda suite: len(suite.get_tests()) > 0, suites),
        key=lambda suite: suite.duration,
        reverse=True
    )


def get_total_duration(elems):
    return reduce(lambda x, y: x + y, [elem.duration for elem in elems], 0)


def format_test_entry(elem, total_time):
    if elem.duration is not None:
        return (
            elem.path,
            humanize_duration(elem.duration, show_milliseconds=True),
            "%d%%" % (elem.duration / total_time * 100)
        )
    else:
        return elem.path, "-", "-"


def get_top_tests(suites):
    tests = get_tests_ordered_by_duration(flatten_tests(suites))
    total_duration = get_total_duration(tests)
    return [format_test_entry(test, total_duration) for test in tests]


class TopTests(Command):
    def get_name(self):
        return "top-tests"

    def get_description(self):
        return "Display tests ordered by duration"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Top tests")
        add_report_path_cli_arg(group)
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        suites = filter_suites(report.get_suites(), make_report_filter(cli_args))

        print_table(
            "Tests, ordered by duration",
            ("Test", "Duration", "In %"),
            get_top_tests(suites)
        )

        return 0


def get_top_suites(suites):
    processed_suites = get_suites_ordered_by_duration(flatten_suites(suites))
    total_duration = get_total_duration(processed_suites)
    return [format_test_entry(suite, total_duration) for suite in processed_suites]


class TopSuites(Command):
    def get_name(self):
        return "top-suites"

    def get_description(self):
        return "Display suites ordered by duration"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Top suites")
        add_report_path_cli_arg(group)
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        suites = filter_suites(report.get_suites(), make_report_filter(cli_args))

        print_table(
            "Suites, ordered by duration",
            ("Suite", "Duration", "In %"),
            get_top_suites(suites)
        )

        return 0


def group_steps_by_description(steps):
    steps_by_description = {}
    for step in steps:
        if step.description not in steps_by_description:
            steps_by_description[step.description] = []
        steps_by_description[step.description].append(step)
    return steps_by_description


def get_steps_min_duration(steps):
    return min(step.duration for step in steps)


def get_steps_max_duration(steps):
    return max(step.duration for step in steps)


def get_steps_average_duration(steps):
    return get_total_duration(steps) / len(steps)


def format_steps_aggregation(description, occurrences, min_duration, max_duration, average_duration, duration, duration_pct):
    return (
        description,
        str(occurrences),
        humanize_duration(min_duration, show_milliseconds=True),
        humanize_duration(max_duration, show_milliseconds=True),
        humanize_duration(average_duration, show_milliseconds=True),
        humanize_duration(duration, show_milliseconds=True),
        "%d%%" % duration_pct
    )


def get_steps_aggregation(steps):
    steps_by_description = group_steps_by_description(steps)
    total_duration = get_total_duration(steps)

    data = []
    for description, steps in steps_by_description.items():
        duration = get_total_duration(steps)
        data.append([
            description,
            len(steps),
            get_steps_min_duration(steps),
            get_steps_max_duration(steps),
            get_steps_average_duration(steps),
            duration,
            duration / total_duration * 100
        ])

    return sorted(data, key=lambda row: row[-2], reverse=True)


def get_top_steps(suites):
    steps_aggregation = get_steps_aggregation(list(flatten_steps(suites)))
    return [format_steps_aggregation(*agg) for agg in steps_aggregation]


class TopSteps(Command):
    def get_name(self):
        return "top-steps"

    def get_description(self):
        return "Display steps aggregated and ordered by duration"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Top steps")
        add_report_path_cli_arg(group)
        add_report_filter_cli_args(cli_parser, no_positional_argument=True)

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        suites = filter_suites(report.get_suites(), make_report_filter(cli_args))

        print_table(
            "Steps, aggregated and ordered by duration",
            ("Step", "Occ.", "Min.", "Max", "Avg.", "Total", "In %"),
            get_top_steps(suites)
        )

        return 0
