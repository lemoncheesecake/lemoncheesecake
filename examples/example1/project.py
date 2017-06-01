import os

from lemoncheesecake.testsuite import load_testsuites_from_directory
from lemoncheesecake.fixtures import load_fixtures_from_directory
from lemoncheesecake.reporting import reportdir
from lemoncheesecake.reporting.backend import SAVE_AT_EACH_EVENT
from lemoncheesecake.reporting.backends import ConsoleBackend, JsonBackend, XmlBackend, HtmlBackend

project_dir = os.path.dirname(__file__)
TESTSUITES = load_testsuites_from_directory(os.path.join(project_dir, "suites"))
FIXTURES = load_fixtures_from_directory(os.path.join(project_dir, "fixtures"))

def fail(dummy):
    raise Exception("operation has failed")

###
# Reporting
###
console_backend = ConsoleBackend()
json_backend = JsonBackend()
json_backend.save_mode = SAVE_AT_EACH_EVENT
xml_backend = XmlBackend()
html_backend = HtmlBackend()

REPORTING_BACKENDS = console_backend, json_backend, xml_backend, html_backend
REPORTING_BACKENDS_ACTIVE = console_backend.name, json_backend.name, html_backend.name
REPORT_DIR_CREATION = lambda top_dir: reportdir.report_dir_with_archiving(top_dir, reportdir.archive_dirname_datetime)

# Test run hooks
def before_tests(report_dir):
    pass
RUN_HOOK_BEFORE_TESTS = before_tests

def after_tests(report_dir):
    pass
RUN_HOOK_AFTER_TESTS = after_tests
