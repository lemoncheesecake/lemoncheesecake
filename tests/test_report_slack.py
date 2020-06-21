import pytest
from pytest_mock import mocker

from helpers.utils import env_vars
from helpers.runner import run_suite_class
from helpers.cli import cmdout
import lemoncheesecake.api as lcc
from lemoncheesecake.reporting.backends.slack import SlackReportingBackend
from lemoncheesecake.exceptions import UserError


def _test_reporting_session(**vars):
    backend = SlackReportingBackend()
    with env_vars(**vars):
        return backend.create_reporting_session(None, None, None, None)


@pytest.fixture
def slacker_mock(mocker):
    mocker.patch("slacker.Slacker")
    return mocker


@lcc.suite("suite")
class suite_sample:
    @lcc.test("test")
    def test(self):
        lcc.log_info("do stuff")


try:
    import slacker
except ImportError:
    pass  # slacker is not installed (slack is an optional feature), skip tests
else:
    def test_create_reporting_session_success(tmpdir):
        _test_reporting_session(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan")


    def test_create_reporting_session_missing_config(tmpdir):
        with pytest.raises(UserError, match="missing environment variable"):
            _test_reporting_session(LCC_SLACK_AUTH_TOKEN=None, LCC_SLACK_CHANNEL=None)


    def test_create_reporting_session_message_variable_ok(tmpdir):
        _test_reporting_session(
            LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan",
            LCC_SLACK_MESSAGE_TEMPLATE="result: {passed_pct}"
        )


    def test_create_reporting_session_bad_message_variable(tmpdir):
        with pytest.raises(UserError, match="unknown variable"):
            _test_reporting_session(
                LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan",
                LCC_SLACK_MESSAGE_TEMPLATE="result: {unknown_var}"
            )


    def test_reporting_session(slacker_mock):
        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        slacker.Slacker.assert_called_once_with("sometoken", http_proxy=None, https_proxy=None)

        post_message = slacker.Slacker.return_value.chat.post_message
        assert post_message.call_args[0][0] == "#chan"
        assert "1 passed" in post_message.call_args[0][1]
        assert "0 failed" in post_message.call_args[0][1]


    def test_reporting_session_custom_proxy(slacker_mock):
        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan", LCC_SLACK_HTTP_PROXY="http://my.proxy"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        slacker.Slacker.assert_called_once_with("sometoken", http_proxy="http://my.proxy", https_proxy="http://my.proxy")


    def test_reporting_session_custom_message_template(slacker_mock):
        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan", LCC_SLACK_MESSAGE_TEMPLATE="{passed_pct}"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        assert slacker.Slacker.return_value.chat.post_message.call_args[0][1] == "100%"


    def test_reporting_session_notify_failure_with_test_passed(slacker_mock):
        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan", LCC_SLACK_ONLY_NOTIFY_FAILURE="yes"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        slacker.Slacker.return_value.chat.post_message.assert_not_called()


    def test_reporting_session_notify_failure_with_test_failed(slacker_mock):
        @lcc.suite("suite")
        class suite_sample:
            @lcc.test("test")
            def test(self):
                lcc.log_error("something wrong happened")

        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan", LCC_SLACK_ONLY_NOTIFY_FAILURE="yes"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        assert len(slacker.Slacker.return_value.chat.post_message.mock_calls) == 1


    def test_reporting_session_notification_error(slacker_mock, cmdout):
        def _raise_error(_, __):
            raise slacker.Error("Could not send message")
        slacker.Slacker.return_value.chat.post_message.side_effect = _raise_error

        with env_vars(LCC_SLACK_AUTH_TOKEN="sometoken", LCC_SLACK_CHANNEL="#chan"):
            run_suite_class(suite_sample, backends=[SlackReportingBackend()])

        cmdout.assert_substrs_anywhere(("Could not send message",), on_stderr=True)
