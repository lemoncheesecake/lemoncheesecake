from __future__ import print_function

import os
import time

try:
    import slacker
    SLACKER_IS_AVAILABLE = True
except ImportError:
    SLACKER_IS_AVAILABLE = False

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.exceptions import UserError
from lemoncheesecake.utils import humanize_duration


class BaseSlackReportingSession(ReportingSession):
    def __init__(self, auth_token, channel):
        self.slack = slacker.Slacker(auth_token)
        self.channel = channel

    def send_message(self, message):
        try:
            self.slack.chat.post_message(self.channel, message)
        except slacker.Error as excp:
            raise UserError("Error while notifying Slack channel/user '%s', got: %s" % (
                self.channel, excp
            ))


class EndOfTestsNotifier(BaseSlackReportingSession):
    def __init__(self, auth_token, channel, message_template, only_notify_failure=False):
        BaseSlackReportingSession.__init__(self, auth_token, channel)
        self.message_template = message_template
        self.only_notify_failure = only_notify_failure

    def build_message_parameters(self, report, stats):
        enabled_tests = stats.get_enabled_tests()

        def percent(val, of):
            return "%d%%" % ((float(val) / of * 100) if of else 0)

        return {
            "start_time": time.asctime(time.localtime(report.start_time)),
            "end_time": time.asctime(time.localtime(report.end_time)),
            "duration": humanize_duration(report.end_time - report.start_time),

            "total": stats.tests,
            "enabled": enabled_tests,

            "passed": stats.test_statuses["passed"],
            "passed_pct": percent(stats.test_statuses["passed"], of=enabled_tests),

            "failed": stats.test_statuses["failed"],
            "failed_pct": percent(stats.test_statuses["failed"], of=enabled_tests),

            "skipped": stats.test_statuses["skipped"],
            "skipped_pct": percent(stats.test_statuses["skipped"], of=enabled_tests),

            "disabled": stats.test_statuses["disabled"],
            "disabled_pct": percent(stats.test_statuses["disabled"], of=stats.tests)
        }

    def on_tests_ending(self, report):
        stats = report.get_stats()
        if self.only_notify_failure and stats.is_successful():
            return

        message = self.message_template.format(**self.build_message_parameters(report, stats))

        self.send_message(message)


def get_env_var(name, optional=False, default=None):
    try:
        return os.environ[name]
    except KeyError as excp:
        if optional:
            return default
        else:
            raise UserError("Slack reporting backend, cannot get environment variable %s" % excp)


def get_slack_auth_token():
    return get_env_var("SLACK_AUTH_TOKEN")


def get_slack_channel():
    return get_env_var("SLACK_CHANNEL")


def get_message_template():
    return get_env_var(
        "SLACK_MESSAGE_TEMPLATE", optional=True, default="{passed} passed, {failed} failed, {skipped} skipped"
    )


def get_only_notify_on_failure():
    return "SLACK_ONLY_NOTIFY_FAILURE" in os.environ


class SlackReportingBackend(ReportingBackend):
    name = "slack"

    def is_available(self):
        return SLACKER_IS_AVAILABLE

    def create_reporting_session(self, report_dir, report):
        return EndOfTestsNotifier(
            get_slack_auth_token(), get_slack_channel(), get_message_template(),
            get_only_notify_on_failure()
        )
