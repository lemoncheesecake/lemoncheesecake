from __future__ import print_function

import os
import sys

try:
    import slacker
    SLACKER_IS_AVAILABLE = True
except ImportError:
    SLACKER_IS_AVAILABLE = False

from lemoncheesecake.reporting import ReportingBackend, ReportingSession, ReportingSessionBuilderMixin, \
    check_report_message_template
from lemoncheesecake.exceptions import UserError


class SlackReportingSession(ReportingSession):
    def __init__(self, auth_token, channel, message_template, proxy=None, only_notify_failure=False):
        self.slacker = slacker.Slacker(auth_token, http_proxy=proxy, https_proxy=proxy)
        self.channel = channel
        self.message_template = message_template
        self.only_notify_failure = only_notify_failure

    def on_test_session_end(self, event):
        if self.only_notify_failure and event.report.is_successful():
            return

        message = event.report.build_message(self.message_template)
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
            raise UserError("Slack reporting backend: missing environment variable '%s'" % excp)


class SlackReportingBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def get_name(self):
        return "slack"

    def is_available(self):
        return SLACKER_IS_AVAILABLE

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        try:
            message_template = check_report_message_template(get_env_var(
                "LCC_SLACK_MESSAGE_TEMPLATE", optional=True,
                default="{passed} passed, {failed} failed, {skipped} skipped"
            ))
        except ValueError as excp:
            raise UserError("Slack reporting backend: %s" % excp)

        return SlackReportingSession(
            auth_token=get_env_var("LCC_SLACK_AUTH_TOKEN"),
            channel=get_env_var("LCC_SLACK_CHANNEL"),
            message_template=message_template,
            proxy=get_env_var("LCC_SLACK_HTTP_PROXY", optional=True, default=None),
            only_notify_failure="LCC_SLACK_ONLY_NOTIFY_FAILURE" in os.environ
        )
