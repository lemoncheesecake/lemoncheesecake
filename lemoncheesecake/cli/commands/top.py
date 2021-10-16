from functools import reduce

from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.helpers.text import ensure_single_line_text
from lemoncheesecake.helpers.console import print_table
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, add_report_path_cli_arg, get_report_path
from lemoncheesecake.reporting import load_report
from lemoncheesecake.filter import add_result_filter_cli_args, make_result_filter, \
    add_step_filter_cli_args, make_step_filter
from lemoncheesecake.testtree import flatten_suites, filter_suites


def get_total_duration(elems):
    return reduce(lambda x, y: x + y, (elem.duration or 0 for elem in elems), 0)


class TopTests(Command):
    def get_name(self):
        return "top-tests"

    def get_description(self):
        return "Display tests ordered by duration"

    def add_cli_args(self, cli_parser):
        add_result_filter_cli_args(cli_parser, only_executed_tests=True)
        group = cli_parser.add_argument_group("Top tests")
        add_report_path_cli_arg(group)

    @staticmethod
    def _get_tests_ordered_by_duration(tests):
        return sorted(tests, key=lambda test: test.duration, reverse=True)

    @staticmethod
    def _format_test_entry(test, total_time):
        if test.duration is not None:
            return (
                test.path,
                humanize_duration(test.duration, show_milliseconds=True),
                "%d%%" % (test.duration / total_time * 100) if total_time else 100
            )
        else:
            return test.path, "-", "-"

    @staticmethod
    def get_top_tests(report, test_filter):
        tests = TopTests._get_tests_ordered_by_duration(filter(test_filter, report.all_tests()))
        total_duration = get_total_duration(tests)
        return [TopTests._format_test_entry(test, total_duration) for test in tests]

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        test_filter = make_result_filter(cli_args, only_executed_tests=True)

        print_table(
            "Tests, ordered by duration",
            ("Test", "Duration", "In %"),
            TopTests.get_top_tests(report, test_filter)
        )

        return 0


class TopSuites(Command):
    def get_name(self):
        return "top-suites"

    def get_description(self):
        return "Display suites ordered by duration"

    def add_cli_args(self, cli_parser):
        add_result_filter_cli_args(cli_parser, only_executed_tests=True)
        group = cli_parser.add_argument_group("Top suites")
        add_report_path_cli_arg(group)

    @staticmethod
    def _get_suites_ordered_by_duration(suites):
        return sorted(
            filter(lambda s: any((s.get_tests(), s.suite_setup, s.suite_teardown)), suites),
            key=lambda suite: suite.duration,
            reverse=True
        )

    @staticmethod
    def _format_suite_entry(suite, total_time):
        if suite.duration is not None:
            return (
                suite.path,
                len(suite.get_tests()),
                humanize_duration(suite.duration, show_milliseconds=True),
                "%d%%" % ((suite.duration / total_time * 100) if total_time else 100)
            )
        else:
            return suite.path, len(suite.get_tests()), "-", "-"

    @staticmethod
    def get_top_suites(report, result_filter):
        processed_suites = TopSuites._get_suites_ordered_by_duration(
            flatten_suites(filter_suites(report.get_suites(), result_filter))
        )
        total_duration = get_total_duration(processed_suites)
        return [TopSuites._format_suite_entry(suite, total_duration) for suite in processed_suites]

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        result_filter = make_result_filter(cli_args, only_executed_tests=True)

        print_table(
            "Suites, ordered by duration",
            ("Suite", "Tests Nb.", "Duration", "In %"),
            TopSuites.get_top_suites(report, result_filter)
        )

        return 0


class TopSteps(Command):
    def get_name(self):
        return "top-steps"

    def get_description(self):
        return "Display steps aggregated and ordered by duration"

    def add_cli_args(self, cli_parser):
        add_step_filter_cli_args(cli_parser)
        group = cli_parser.add_argument_group("Top steps")
        add_report_path_cli_arg(group)

    @staticmethod
    def _group_steps_by_description(steps):
        steps_by_description = {}
        for step in steps:
            description = ensure_single_line_text(step.description)
            if description not in steps_by_description:
                steps_by_description[description] = []
            steps_by_description[description].append(step)
        return steps_by_description

    @staticmethod
    def _get_steps_min_duration(steps):
        return min(step.duration or 0 for step in steps)

    @staticmethod
    def _get_steps_max_duration(steps):
        return max(step.duration or 0 for step in steps)

    @staticmethod
    def _get_steps_average_duration(steps):
        return get_total_duration(steps) / len(steps)

    @staticmethod
    def _format_steps_aggregation(description, occurrences, min_duration, max_duration, average_duration, duration,
                                  duration_pct):
        return (
            description,
            str(occurrences),
            humanize_duration(min_duration, show_milliseconds=True),
            humanize_duration(max_duration, show_milliseconds=True),
            humanize_duration(average_duration, show_milliseconds=True),
            humanize_duration(duration, show_milliseconds=True),
            "%d%%" % duration_pct
        )

    @staticmethod
    def _get_steps_aggregation(steps):
        steps_by_description = TopSteps._group_steps_by_description(steps)
        total_duration = get_total_duration(steps)

        data = []
        for description, steps in steps_by_description.items():
            duration = get_total_duration(steps)
            data.append([
                description,
                len(steps),
                TopSteps._get_steps_min_duration(steps),
                TopSteps._get_steps_max_duration(steps),
                TopSteps._get_steps_average_duration(steps),
                duration,
                (duration / total_duration * 100) if total_duration else 100
            ])

        return sorted(data, key=lambda row: row[-2], reverse=True)

    @staticmethod
    def get_top_steps(report, step_filter):
        steps = list(filter(step_filter, report.all_steps()))
        steps_aggregation = TopSteps._get_steps_aggregation(steps)
        return [TopSteps._format_steps_aggregation(*agg) for agg in steps_aggregation]

    def run_cmd(self, cli_args):
        report_path = get_report_path(cli_args)

        report = load_report(report_path, auto_detect_reporting_backends())
        step_filter = make_step_filter(cli_args)

        print_table(
            "Steps, aggregated and ordered by duration",
            ("Step", "Occ.", "Min.", "Max", "Avg.", "Total", "In %"),
            TopSteps.get_top_steps(report, step_filter)
        )

        return 0
