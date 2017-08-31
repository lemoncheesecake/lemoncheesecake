'''
Created on Sep 30, 2016

@author: nicolas
'''

from __future__ import print_function

import os
import os.path as osp
import sys
import tempfile
import shutil
import re

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite.loader import load_suites_from_classes, load_suite_from_file
from lemoncheesecake import runner
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake import reporting
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string
from lemoncheesecake.fixtures import FixtureRegistry, load_fixtures_from_func
from lemoncheesecake.project import create_project
from lemoncheesecake.filter import filter_suites

def build_test_module(name="mysuite"):
    return """
import lemoncheesecake.api as lcc

@lcc.suite("Test Suite")
class {name}:
    @lcc.test("This is a test")
    def test_{name}(self):
        pass
""".format(name=name)


def build_fixture_module(name="myfixture"):
    return """
import lemoncheesecake.api as lcc

@lcc.fixture()
def {name}():
    pass
""".format(name=name)


def build_test_project(params={}, extra_imports=[], static_content=""):
    return """
from lemoncheesecake.reporting import backends
from lemoncheesecake.fixtures import load_fixtures_from_file, load_fixtures_from_files, load_fixtures_from_directory
from lemoncheesecake.suite.loader import *

from lemoncheesecake import validators

{EXTRA_IMPORTS}

{STATIC_CONTENT}

{PARAMS}
""".format(
    PARAMS="\n".join(["%s = %s" % (p, v) for p, v in params.items()]),
    EXTRA_IMPORTS="\n".join(extra_imports),
    STATIC_CONTENT=static_content
)


def _remove_py_file(filename):
    os.unlink(filename)
    if osp.exists(filename + "c"):
        os.unlink(filename + "c")
    if osp.exists(filename + "o"):
        os.unlink(filename + "o")


def build_suite_from_module(module_content):
    fd, filename = tempfile.mkstemp(suffix=".py")
    fh = open(filename, "w")
    fh.write("import lemoncheesecake.api as lcc\n\n")
    fh.write("SUITE = {'description': 'My Suite'}\n\n")
    fh.write(module_content)
    fh.close()
    os.close(fd)
    suite = load_suite_from_file(filename)
    _remove_py_file(filename)

    return suite


def generate_project(project_dir, module_name, module_content, fixtures_content=None):
    create_project(project_dir)
    with open(osp.join(project_dir, "suites", "%s.py" % module_name), "w") as fh:
        fh.write(module_content)
    if fixtures_content:
        with open(osp.join(project_dir, "fixtures", "fixtures.py"), "w") as fh:
            fh.write(fixtures_content)


def build_fixture_registry(*funcs):
    registry = FixtureRegistry()
    for func in funcs:
        registry.add_fixtures(load_fixtures_from_func(func))
    return registry


class TestReportingSession(reporting.ReportingSession):
    def __init__(self):
        self._test_statuses = {}
        self.last_test_status = None
        self.test_nb = 0
        self.check_nb = 0
        self.check_success_nb = 0
        self.check_failing_nb = 0
        self.test_failing_nb = 0
        self.test_success_nb = 0
        self.last_log = None
        self.last_test = None
        self.last_check_description = None
        self.last_check_outcome = None
        self.last_check_details = None
        self.error_log_nb = 0
        self.backend = None

    def get_last_test(self):
        return self.last_test

    def get_last_test_status(self):
        return self.last_test_status

    def get_last_test_outcome(self):
        return self.get_last_test_status() == "passed"

    def get_last_log(self):
        return self.last_log

    def get_error_log_nb(self):
        return self.error_log_nb

    def get_test_status(self, test_name):
        return self._test_statuses[test_name]

    def get_test_outcome(self, test_name):
        return self.get_test_status(test_name) == "passed"

    def get_last_check(self):
        return self.last_check_description, self.last_check_outcome, self.last_check_details

    def get_failing_test_nb(self):
        return self.test_failing_nb

    def get_successful_test_nb(self):
        return self.test_success_nb

    def begin_test(self, test):
        self.last_test_outcome = None

    def end_test(self, test):
        self.last_test = test.name
        self._test_statuses[test.name] = test.status
        self.last_test_status = test.status
        self.test_nb += 1
        if test.status == "passed":
            self.test_success_nb += 1
        else:
            self.test_failing_nb += 1

    def bypass_test(self, test):
        self.end_test(test)

    def log(self, level, content):
        if level == "error":
            self.error_log_nb += 1
        self.last_log = content

    def check(self, description, outcome, details=None):
        self.check_nb += 1
        if outcome:
            self.check_success_nb += 1
        else:
            self.check_failing_nb += 1
        self.last_check_description = description
        self.last_check_outcome = outcome
        self.last_check_details = details


_reporting_session = None

class TestReportingBackend(reporting.ReportingBackend):
    name = "test_backend"

    def __init__(self, reporting_session):
        self.reporting_session = reporting_session

    def create_reporting_session(self, report, report_dir):
        return self.reporting_session


def get_reporting_session():
    global _reporting_session
    _reporting_session = TestReportingSession()
    return _reporting_session


@pytest.fixture()
def reporting_session():
    return get_reporting_session()


def run_suites(suites, filter=None, fixtures=None, backends=None, tmpdir=None, stop_on_failure=False):
    global _reporting_session

    if fixtures == None:
        fixture_registry = FixtureRegistry()
    else:
        if isinstance(fixtures, FixtureRegistry):
            fixture_registry = fixtures
        else:
            fixture_registry = build_fixture_registry(*fixtures)

    if not backends:
        backends = []

    if _reporting_session:
        backends.append(TestReportingBackend(_reporting_session))

    if filter:
        suites = filter_suites(suites, filter)

    if tmpdir:
        try:
            runner.run_suites(suites, fixture_registry, backends, tmpdir.strpath, stop_on_failure=stop_on_failure)
        finally:
            _reporting_session = None
    else:
        report_dir = tempfile.mkdtemp()
        try:
            runner.run_suites(suites, fixture_registry, backends, report_dir, stop_on_failure=stop_on_failure)
        finally:
            shutil.rmtree(report_dir)
            # reset _reporting_session (either it has been set or not) at the end of each test run
            _reporting_session = None

    report = get_runtime().report
    dump_report(report)

    return report


def run_suite_classes(suite_classes, filter=None, fixtures=None, backends=None, tmpdir=None, stop_on_failure=False):
    suites = load_suites_from_classes(suite_classes)
    return run_suites(suites, filter=filter, fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


def run_suite(suite, filter=None, fixtures=None, backends=[], tmpdir=None, stop_on_failure=False):
    return run_suites([suite], filter=filter, fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


def run_suite_class(suite_class, filter=None, fixtures=None, backends=[], tmpdir=None, stop_on_failure=False):
    suite = load_suite_from_class(suite_class)
    return run_suite(suite, filter=filter, fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


def run_func_in_test(callback):
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            callback()

    return run_suite_class(MySuite)


def dump_report(report):
    try:
        import lxml
    except ImportError:
        pass
    else:
        xml = serialize_report_as_string(report)
        print(xml, file=sys.stderr)


def dummy_test_callback():
    def wrapped(suite):
        pass
    return wrapped


def assert_check_data(actual, expected):
    assert actual.description == expected.description
    assert actual.outcome == expected.outcome
    assert actual.details == expected.details


def assert_log_data(actual, expected):
    assert actual.level == expected.level
    assert actual.message == expected.message
    assert round(actual.time, 3) == round(expected.time, 3)


def assert_attachment_data(actual, expected):
    assert actual.description == expected.description
    assert actual.filename == expected.filename


def assert_url_data(actual, expected):
    assert actual.description == expected.description
    assert actual.url == expected.url


def assert_step_data(actual, expected):
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)
    assert actual.description == expected.description
    assert len(actual.entries) == len(expected.entries)
    for actual_entry, expected_entry in zip(actual.entries, expected.entries):
        assert actual_entry.__class__ == expected_entry.__class__
        if isinstance(actual_entry, reporting.LogData):
            assert_log_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.CheckData):
            assert_check_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.AttachmentData):
            assert_attachment_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.UrlData):
            assert_url_data(actual_entry, expected_entry)
        else:
            raise Exception("Unknown class '%s'" % actual.__class__.__name__)


def assert_test_data(actual, expected):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links
    assert actual.status == expected.status
    assert actual.status_details == expected.status_details
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)

    assert len(actual.steps) == len(expected.steps)
    for actual_step, expected_step in zip(actual.steps, expected.steps):
        assert_step_data(actual_step, expected_step)


def assert_hook_data(actual, expected):
    if expected == None:
        assert actual == None
    else:
        assert actual.outcome == expected.outcome
        assert round(actual.start_time, 3) == round(expected.start_time, 3)
        assert round(actual.end_time, 3) == round(expected.end_time, 3)
        assert len(actual.steps) == len(expected.steps)
        for actual_step, expected_step in zip(actual.steps, expected.steps):
            assert_step_data(actual_step, expected_step)


def assert_suite_data(actual, expected):
    assert actual.name == expected.name
    assert actual.description == expected.description
    if expected.parent_suite == None:
        assert actual.parent_suite == None
    else:
        assert actual.parent_suite.name == expected.parent_suite.name
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links

    assert_hook_data(actual.suite_setup, expected.suite_setup)

    assert len(actual.get_tests()) == len(expected.get_tests())
    for actual_test, expected_test in zip(actual.get_tests(), expected.get_tests()):
        assert_test_data(actual_test, expected_test)

    assert len(actual.get_suites()) == len(expected.get_suites())
    for actual_subsuite, expected_subsuite in zip(actual.get_suites(), expected.get_suites()):
        assert_suite_data(actual_subsuite, expected_subsuite)

    assert_hook_data(actual.suite_teardown, expected.suite_teardown)


def assert_report(actual, expected):
    assert actual.info == expected.info
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)
    assert round(actual.report_generation_time, 3) == round(expected.report_generation_time, 3)
    assert len(actual.suites) == len(expected.suites)

    assert_hook_data(actual.test_session_setup, expected.test_session_setup)

    for actual_suite, expected_suite in zip(actual.suites, expected.suites):
        assert_suite_data(actual_suite, expected_suite)

    assert_hook_data(actual.test_session_teardown, expected.test_session_teardown)


def assert_steps_data(steps):
    for step in steps:
        assert step.start_time
        assert step.end_time >= step.start_time


def assert_test_data_from_test(test_data, test):
    assert test_data.name == test.name
    assert test_data.description == test.description
    assert test_data.tags == test.tags
    assert test_data.properties == test.properties
    assert test_data.links == test.links

    assert_steps_data(test_data.steps)


def assert_suite_data_from_suite(suite_data, suite):
    assert suite_data.name == suite.name
    assert suite_data.description == suite.description
    assert suite_data.tags == suite.tags
    assert suite_data.properties == suite.properties
    assert suite_data.links == suite.links

    if suite.has_hook("setup_suite"):
        assert suite_data.suite_setup != None
        assert suite_data.suite_setup.start_time != None
        assert suite_data.suite_setup.end_time != None
        assert_steps_data(suite_data.suite_setup.steps)

    assert len(suite_data.get_tests()) == len(suite.get_tests())
    for test_data, test in zip(suite_data.get_tests(), suite.get_tests()):
        assert_test_data_from_test(test_data, test)

    assert len(suite_data.get_suites()) == len(suite.get_suites())
    for sub_suite_data, sub_suite in zip(suite_data.get_suites(), suite.get_suites()):
        assert_suite_data_from_suite(sub_suite_data, sub_suite)

    if suite.has_hook("teardown_suite"):
        assert suite_data.suite_teardown != None
        assert suite_data.suite_teardown.start_time != None
        assert suite_data.suite_teardown.end_time != None
        assert_steps_data(suite_data.suite_teardown.steps)


def assert_report_from_suites(report, suite_classes):
    assert report.start_time != None
    assert report.end_time != None
    assert report.report_generation_time != None
    assert len(report.suites) == len(suite_classes)
    for suite_data, suite_class in zip(report.suites, suite_classes):
        suite = load_suite_from_class(suite_class)
        assert_suite_data_from_suite(suite_data, suite)


def assert_report_from_suite(report, suite_class):
    assert_report_from_suites(report, [suite_class])


def assert_report_stats(report,
                        expected_test_successes=0, expected_test_failures=0, expected_test_skippeds=0,
                        expected_errors=0,
                        expected_check_successes=0, expected_check_failures=0,
                        expected_error_logs=0, expected_warning_logs=0):
    stats = report.get_stats()
    assert stats.tests == expected_test_successes + expected_test_failures + expected_test_skippeds
    assert stats.test_statuses["passed"] == expected_test_successes
    assert stats.test_statuses["failed"] == expected_test_failures
    assert stats.test_statuses["skipped"] == expected_test_skippeds
    assert stats.errors == expected_errors
    assert stats.checks == expected_check_successes + expected_check_failures
    assert stats.check_successes == expected_check_successes
    assert stats.check_failures == expected_check_failures
    assert stats.error_logs == expected_error_logs
    assert stats.warning_logs == expected_warning_logs


@pytest.fixture()
def cmdout(capsys):
    class _CmdOutput:
        def __init__(self):
            self._stdout_lines = None
            self._stderr_lines = None

        def get_lines(self, on_stderr=False):
            if self._stdout_lines == None or self._stderr_lines == None:
                stdout, stderr = capsys.readouterr()
                self._stdout_lines = [line for line in stdout.split("\n") if line != ""]
                self._stderr_lines = [line for line in stderr.split("\n") if line != ""]
            return self._stderr_lines if on_stderr else self._stdout_lines

        def assert_substrs_in_line(self, line_nb, substrs, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for substr in substrs:
                assert substr in lines[line_nb]

        def assert_substrs_not_in_line(self, line_nb, substrs, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for substr in substrs:
                assert substr not in lines[line_nb]

        def assert_line_startswith(self, line_nb, substr, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert lines[line_nb].startswith(substr)

        def assert_line_not_startswith(self, line_nb, substr, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert not lines[line_nb].startswith(substr)

        def assert_lines_nb(self, lines_nb, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert len(lines) == lines_nb

        def assert_lines_match(self, pattern, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for line in lines:
                if re.compile(pattern).search(line):
                    return
            raise Exception("No line matches pattern '%s' in \n<<<\n%s\n>>>" % (pattern, "\n".join(lines)))

        def dump(self):
            stdout = self.get_lines()
            stderr = self.get_lines(on_stderr=True)
            print("STDOUT:\n<<<\n%s\n>>>\n" % "\n".join(stdout))
            print("STDERR:\n<<<\n%s\n>>>\n" % "\n".join(stderr))

    return _CmdOutput()


def assert_match_result(matcher, actual, result_outcome, result_details):
    result_details_lst = result_details if type(result_details) in (list, tuple) else [result_details]
    
    reporting_session = get_reporting_session()
    run_func_in_test(lambda: lcc.check_that("value", actual, matcher))
    assert reporting_session.last_check_outcome == result_outcome
    for details in result_details_lst:
        assert details in reporting_session.last_check_details


def assert_match_success(matcher, actual, result_details):
    assert_match_result(matcher, actual, True, result_details)


def assert_match_failure(matcher, actual, result_details):
    assert_match_result(matcher, actual, False, result_details)


def assert_run_output(cmdout, suite_name, successful_tests=[], failed_tests=[], skipped_tests=[]):
    cmdout.assert_lines_match("= %s =" % suite_name)
    for test in successful_tests:
        cmdout.assert_lines_match("OK.+%s" % test)
    for test in failed_tests + skipped_tests:
        cmdout.assert_lines_match("KO.+%s" % test)
    cmdout.assert_lines_match("Tests: %d" % (len(successful_tests + failed_tests + skipped_tests)))
    cmdout.assert_lines_match("Successes: %d" % len(successful_tests))
    cmdout.assert_lines_match("Failures: %d" % len(failed_tests))
    if len(skipped_tests) > 0:
        cmdout.assert_lines_match("Skipped: %d" % len(skipped_tests))