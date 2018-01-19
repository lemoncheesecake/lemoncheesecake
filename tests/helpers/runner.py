from __future__ import print_function

import os
import os.path as osp
import sys
import tempfile
import shutil

import pytest

from lemoncheesecake.suite.loader import load_suites_from_classes, load_suite_from_file
from lemoncheesecake import runner
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string
from lemoncheesecake.fixtures import FixtureRegistry, load_fixtures_from_func
from lemoncheesecake.project import create_project
from lemoncheesecake import events
from lemoncheesecake.cli import main
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake import reporting
import lemoncheesecake.api as lcc


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

    def on_test_beginning(self, test):
        self.last_test_outcome = None

    def on_test_ending(self, test, status):
        self.last_test = test.name
        self._test_statuses[test.name] = status
        self.last_test_status = status
        self.test_nb += 1
        if status == "passed":
            self.test_success_nb += 1
        else:
            self.test_failing_nb += 1

    def on_disabled_test(self, test):
        self.on_test_ending(test, "disabled")

    def on_skipped_test(self, test, reason):
        self.on_test_ending(test, "skipped")

    def on_log(self, level, content):
        if level == "error":
            self.error_log_nb += 1
        self.last_log = content

    def on_check(self, description, outcome, details=None):
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


def run_suites(suites, fixtures=None, backends=None, tmpdir=None, stop_on_failure=False):
    global _reporting_session

    if fixtures is None:
        fixture_registry = FixtureRegistry()
    else:
        if isinstance(fixtures, FixtureRegistry):
            fixture_registry = fixtures
        else:
            fixture_registry = build_fixture_registry(*fixtures)

    if backends is None:
        backends = []

    if _reporting_session is not None:
        backends = backends + [TestReportingBackend(_reporting_session)]

    events.reset()

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


def run_suite_classes(suite_classes, fixtures=None, backends=None, tmpdir=None, stop_on_failure=False):
    suites = load_suites_from_classes(suite_classes)
    return run_suites(suites, fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


def run_suite(suite, fixtures=None, backends=[], tmpdir=None, stop_on_failure=False):
    return run_suites([suite], fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


def run_suite_class(suite_class, filter=None, fixtures=None, backends=[], tmpdir=None, stop_on_failure=False):
    suite = load_suite_from_class(suite_class)
    return run_suite(suite, fixtures=fixtures, backends=backends, tmpdir=tmpdir, stop_on_failure=stop_on_failure)


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


def run_main(args):
    events.reset()
    return main(args)
