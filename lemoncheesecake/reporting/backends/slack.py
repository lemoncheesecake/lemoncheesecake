from __future__ import print_function

import os
import sys
import time

try:
    import slacker
    SLACKER_IS_AVAILABLE = True
except ImportError:
    SLACKER_IS_AVAILABLE = False

from lemoncheesecake.reporting import ReportingBackend, ReportingSession, ReportingSessionBuilderMixin, ReportStats
from lemoncheesecake.exceptions import UserError
from lemoncheesecake.helpers.time import humanize_duration


def percent(val, of):
    return "%d%%" % ((float(val) / of * 100) if of else 0)


def get_message_template_parameters():
    return {
        "start_time": lambda report, stats: time.asctime(time.localtime(report.start_time)),
        "end_time": lambda report, stats: time.asctime(time.localtime(report.end_time)),
        "duration": lambda report, stats: humanize_duration(report.end_time - report.start_time),

        "total": lambda report, stats: stats.tests_nb,
        "enabled": lambda report, stats: stats.tests_enabled_nb,

        "passed": lambda report, stats: stats.tests_nb_by_status["passed"],
        "passed_pct": lambda report, stats: percent(stats.tests_nb_by_status["passed"], of=stats.tests_enabled_nb),

        "failed": lambda report, stats: stats.tests_nb_by_status["failed"],
        "failed_pct": lambda report, stats: percent(stats.tests_nb_by_status["failed"], of=stats.tests_enabled_nb),

        "skipped": lambda report, stats: stats.tests_nb_by_status["skipped"],
        "skipped_pct": lambda report, stats: percent(stats.tests_nb_by_status["skipped"], of=stats.tests_enabled_nb),

        "disabled": lambda report, stats: stats.tests_nb_by_status["disabled"],
        "disabled_pct": lambda report, stats: percent(stats.tests_nb_by_status["disabled"], of=stats.tests_nb)
    }


def build_message_parameters(report):
    stats = ReportStats.from_report(report)
    return {
        name: func(report, stats) for name, func in get_message_template_parameters().items()
    }


def validate_message_template_validity(template):
    try:
        template.format(**{name: "" for name in get_message_template_parameters()})
        return template
    except KeyError as excp:
        raise UserError("Invalid Slack message template, unknown variable: %s" % excp)


class SlackReportingSession(ReportingSession):
    def __init__(self, auth_token, channel, message_template, proxy=None, only_notify_failure=False):
        self.slacker = slacker.Slacker(auth_token, http_proxy=proxy, https_proxy=proxy)
        self.channel = channel
        self.message_template = message_template
        self.only_notify_failure = only_notify_failure

    def on_test_session_end(self, event):
        if self.only_notify_failure and event.report.is_successful():
            return

        message = self.message_template.format(**build_message_parameters(event.report))
        try:
            self.slacker.chat.post_message(self.channel, message)
        except slacker.Error as excp:
            print("Error while notifying Slack channel/user '%s', got: %s" % (
                self.channel, excp
            ), file=sys.stderr)


def get_env_var(name, optional=False, default=None):
    try:
        return os.environ[name]
    except KeyError as excp:
        if optional:
            return default
        else:
            raise UserError("Missing environment variable '%s' for Slack reporting backend" % excp)


class SlackReportingBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def get_name(self):
        return "slack"

    def is_available(self):
        return SLACKER_IS_AVAILABLE

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        return SlackReportingSession(
            auth_token=get_env_var("LCC_SLACK_AUTH_TOKEN"),
            channel=get_env_var("LCC_SLACK_CHANNEL"),
            message_template=validate_message_template_validity(get_env_var(
                "LCC_SLACK_MESSAGE_TEMPLATE", optional=True,
                default="{passed} passed, {failed} failed, {skipped} skipped"
            )),
            proxy=get_env_var("LCC_SLACK_HTTP_PROXY", optional=True, default=None),
            only_notify_failure="LCC_SLACK_ONLY_NOTIFY_FAILURE" in os.environ
        )
