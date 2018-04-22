from __future__ import print_function

import os
import sys
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
    def __init__(self, auth_token, channel, proxy=None):
        self.slack = slacker.Slacker(
            auth_token, http_proxy=proxy, https_proxy=proxy
        )
        self.channel = channel
        self.errors = []

    def send_message(self, message):
        try:
            self.slack.chat.post_message(self.channel, message)
        except slacker.Error as excp:
            self.errors.append("Error while notifying Slack channel/user '%s', got: %s" % (
                self.channel, excp
            ))

    def show_errors(self):
        if len(self.errors) == 0:
            return

        print("Slack reporting backend, got the following errors while sending messages:", file=sys.stderr)
        for error in self.errors:
            print("- %s" % error, file=sys.stderr)


def percent(val, of):
    return "%d%%" % ((float(val) / of * 100) if of else 0)


def get_message_template_parameters():
    return {
        "start_time": lambda report, stats: time.asctime(time.localtime(report.start_time)),
        "end_time": lambda report, stats: time.asctime(time.localtime(report.end_time)),
        "duration": lambda report, stats: humanize_duration(report.end_time - report.start_time),

        "total": lambda report, stats: stats.tests,
        "enabled": lambda report, stats: stats.get_enabled_tests(),

        "passed": lambda report, stats: stats.test_statuses["passed"],
        "passed_pct": lambda report, stats: percent(stats.test_statuses["passed"], of=stats.get_enabled_tests()),

        "failed": lambda report, stats: stats.test_statuses["failed"],
        "failed_pct": lambda report, stats: percent(stats.test_statuses["failed"], of=stats.get_enabled_tests()),

        "skipped": lambda report, stats: stats.test_statuses["skipped"],
        "skipped_pct": lambda report, stats: percent(stats.test_statuses["skipped"], of=stats.get_enabled_tests()),

        "disabled": lambda report, stats: stats.test_statuses["disabled"],
        "disabled_pct": lambda report, stats: percent(stats.test_statuses["disabled"], of=stats.tests)
    }


def build_message_parameters(report, stats):
    return {name: func(report, stats) for name, func in get_message_template_parameters().items()}


def build_message_empty_parameters():
    return {name: "" for name in get_message_template_parameters()}


def check_message_template_validity(template):
    try:
        template.format(**build_message_empty_parameters())
    except KeyError as excp:
        raise UserError("Invalid Slack message template, unknown variable: %s" % excp)


class EndOfTestsNotifier(BaseSlackReportingSession):
    def __init__(self, auth_token, channel, message_template, proxy=None, only_notify_failure=False):
        BaseSlackReportingSession.__init__(self, auth_token, channel, proxy=proxy)
        check_message_template_validity(message_template)
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

    def on_test_session_end(self, event):
        stats = event.report.get_stats()
        if self.only_notify_failure and stats.is_successful():
            return

        message = self.message_template.format(**build_message_parameters(event.report, stats))
        self.send_message(message)

        self.show_errors()


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


def get_slack_http_proxy():
    return get_env_var("SLACK_HTTP_PROXY", optional=True, default=None)


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

    def create_reporting_session(self, report_dir, report, parallel=False):
        return EndOfTestsNotifier(
            get_slack_auth_token(), get_slack_channel(), get_message_template(),
            proxy=get_slack_http_proxy(), only_notify_failure=get_only_notify_on_failure()
        )
