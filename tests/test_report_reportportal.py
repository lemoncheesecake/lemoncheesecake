import re
import os.path as osp
import mimetypes

import pytest
from pytest_mock import mocker

from helpers.utils import env_vars
from helpers.runner import run_suite_classes
from helpers.reporttests import ReportingSessionTests

from lemoncheesecake.reporting.backends import ReportPortalBackend
from lemoncheesecake.reporting.report import Log, Check, Attachment, Url
from lemoncheesecake.exceptions import UserError


def _test_reporting_session(**vars):
    backend = ReportPortalBackend()
    with env_vars(**vars):
        return backend.create_reporting_session(None, None, None, None)


@pytest.fixture
def rp_mock(mocker):
    mocker.patch("reportportal_client.RPClient")
    return mocker


def substr(value):
    return re.compile(re.escape(value))


def convert_status(status):
    return "passed" if status == "passed" else "failed"


def make_tags_from_test_tree_node(node):
    return node.tags + \
           ["%s_%s" % (name, value) for name, value in node.properties.items()] + \
           [link[1] or link[0] for link in node.links]


def assert_rp_calls(actual_calls, expected_calls):
    pattern_type = type(re.compile(r"foo"))
    int_as_str_pattern = re.compile(r"^(\d+)$")

    for actual_call, expected_call in zip(actual_calls, expected_calls):
        actual_name, actual_args, actual_kwargs = actual_call
        expected_name, expected_args, expected_kwargs = expected_call
        # method name:
        assert actual_name == expected_name
        # args:
        if actual_name == "log":
            assert int_as_str_pattern.match(actual_args[0]) is not None
            actual_args = actual_args[1:]
        for actual_arg, expected_arg in zip(actual_args, expected_args):
            if type(expected_arg) is pattern_type:
                assert expected_arg.search(actual_arg) is not None
            else:
                assert actual_arg == expected_arg
        # kwargs:
        for name, value in expected_kwargs.items():
            assert actual_kwargs[name] == value
        if actual_name.startswith("start_"):
            assert int_as_str_pattern.match(actual_kwargs["start_time"]) is not None
        if actual_name.startswith("finish_"):
            assert int_as_str_pattern.match(actual_kwargs["end_time"]) is not None

        # TODO: add checks on item_id & parent_item_id

    assert len(actual_calls) == len(expected_calls)


def steps_to_calls(steps):
    for step in steps:
        yield start_test_item("STEP", step.description)
        for log in step.get_logs():
            if isinstance(log, Log):
                yield "log", (log.message, log.level.upper()), {}
            if isinstance(log, Check):
                message = "%s => %s" % (log.description, "OK" if log.is_successful else "NOT OK")
                if log.details:
                    message += "\nDetails: %s" % log.details
                level = "INFO" if log.is_successful else "ERROR"
                yield "log", (message, level), {}
            if isinstance(log, Url):
                yield "log", (substr(log.url), "INFO"), {}
            if isinstance(log, Attachment):
                with open(log.filename, "rb") as fh:
                    attachment_content = fh.read()
                attachment_arg = {
                    "name": osp.basename(log.filename),
                    "data": attachment_content,
                    "mime": mimetypes.guess_type(log.filename)[0] or "application/octet-stream"
                }
                yield "log", (log.description, "INFO"), {"attachment": attachment_arg}
        yield finish_test_item("passed" if step.is_successful() else "failed")


def start_test_item(item_type, name, description=None, tags=None):
    kwargs = {"item_type": item_type, "name": name, "description": description}
    if tags is not None:
        kwargs["tags"] = tags
    return "start_test_item", (), kwargs


def finish_test_item(status):
    return "finish_test_item", (), {"status": status}


def _tests_to_rp_calls(tests):
    for test in tests:
        yield start_test_item("TEST", test.name, test.description, make_tags_from_test_tree_node(test))
        yield from steps_to_calls(test.get_steps())
        yield finish_test_item(test.status)


def suites_to_rp_calls(suites):
    for suite in suites:
        # START SUITE
        yield start_test_item("SUITE", suite.name, suite.description, make_tags_from_test_tree_node(suite))
        # SUITE SETUP
        if suite.suite_setup:
            yield start_test_item("BEFORE_CLASS", "suite_setup", "Suite Setup")
            yield from steps_to_calls(suite.suite_setup.get_steps())
            yield finish_test_item(suite.suite_setup.status)
        # TESTS
        yield from _tests_to_rp_calls(suite.get_tests())
        # SUB SUITES
        yield from suites_to_rp_calls(suite.get_suites())
        # SUITE TEARDOWN
        if suite.suite_teardown:
            yield start_test_item("AFTER_CLASS", "suite_teardown", "Suite Teardown")
            yield from steps_to_calls(suite.suite_teardown.get_steps())
            yield finish_test_item(suite.suite_teardown.status)
        # END SUITE
        yield finish_test_item("passed")


def report_to_rp_calls(report, launch_name="Test Run", launch_description=None):
    yield "start_launch", (), {"name": launch_name, "description": launch_description}

    if report.test_session_setup:
        yield start_test_item("SUITE", "session_setup", "Test Session Setup")
        yield start_test_item("BEFORE_CLASS", "session_setup", "Test Session Setup")
        yield from steps_to_calls(report.test_session_setup.get_steps())
        yield finish_test_item(report.test_session_setup.status)
        yield finish_test_item(report.test_session_setup.status)

    yield from suites_to_rp_calls(report.get_suites())

    if report.test_session_teardown:
        yield start_test_item("SUITE", "session_teardown", "Test Session Teardown")
        yield start_test_item("AFTER_CLASS", "session_teardown", "Test Session Teardown")
        yield from steps_to_calls(report.test_session_teardown.get_steps())
        yield finish_test_item(report.test_session_teardown.status)
        yield finish_test_item(report.test_session_teardown.status)

    yield "finish_launch", (), {}


try:
    import reportportal_client
except ImportError:
    pass  # reportportal_client is not installed (reportportal is an optional feature), skip tests
else:
    @pytest.mark.usefixtures("rp_mock")
    class TestReportPortalReporting(ReportingSessionTests):
        def do_test_reporting_session(self, suites, fixtures=(), report_saving_strategy=None, nb_threads=1):
            if type(suites) not in (list, tuple):
                suites = [suites]
            with env_vars(LCC_RP_URL="http://localhost", LCC_RP_AUTH_TOKEN="sometoken", LCC_RP_PROJECT="myproj"):
                report = run_suite_classes(
                    suites, backends=[ReportPortalBackend()], fixtures=fixtures, tmpdir=".", nb_threads=nb_threads
                )
            assert_rp_calls(
                reportportal_client.RPClient.return_value.mock_calls,
                list(report_to_rp_calls(report))
            )


    def test_create_reporting_session_with_only_required_parameters():
        _test_reporting_session(
            LCC_RP_URL="http://localhost", LCC_RP_AUTH_TOKEN="sometoken",
            LCC_RP_PROJECT="myproj",
            LCC_RP_LAUNCH_NAME=None, LCC_RP_LAUNCH_DESCRIPTION=None
        )


    def test_create_reporting_session_with_all_parameters():
        _test_reporting_session(
            LCC_RP_URL="http://localhost", LCC_RP_AUTH_TOKEN="sometoken",
            LCC_RP_PROJECT="myproj",
            LCC_RP_LAUNCH_NAME="Run", LCC_RP_LAUNCH_DESCRIPTION="Run"
        )


    def test_create_reporting_session_without_parameters():
        with pytest.raises(UserError):
            _test_reporting_session(
                LCC_RP_URL=None, LCC_RP_AUTH_TOKEN=None,
                LCC_RP_PROJECT=None,
                LCC_RP_LAUNCH_NAME=None, LCC_RP_LAUNCH_DESCRIPTION=None
            )
