import os.path

from lemoncheesecake.fixtures import load_fixtures_from_directory
from lemoncheesecake.testsuite import load_testsuites_from_directory
from lemoncheesecake.reporting.backends import ConsoleBackend, JsonBackend, XmlBackend, HtmlBackend
from lemoncheesecake.reporting.reportdir import report_dir_with_archiving, archive_dirname_datetime
from lemoncheesecake.validators import MetadataPolicy

###
# Variables
###
project_dir = os.path.dirname(__file__)

###
# Test suites
###
TESTSUITES = load_testsuites_from_directory(os.path.join(project_dir, "tests"))

###
# Fixtures
###
FIXTURES = load_fixtures_from_directory(os.path.join(project_dir, "fixtures"))

###
# Custom CLI arguments
###
def add_cli_args(cli_parser):
    pass
CLI_EXTRA_ARGS = add_cli_args

###
# Metadata policy
###
mp = MetadataPolicy()
METADATA_POLICY = mp

###
# Reporting
###
console_backend = ConsoleBackend()
json_backend = JsonBackend()
xml_backend = XmlBackend()
html_backend = HtmlBackend()

REPORTING_BACKENDS = console_backend, json_backend, xml_backend, html_backend
REPORTING_BACKENDS_ACTIVE = console_backend.name, json_backend.name, html_backend.name
REPORT_DIR_CREATION = lambda top_dir: report_dir_with_archiving(top_dir, archive_dirname_datetime)

###
# Test run hooks
###
def before_tests(report_dir):
    pass
RUN_HOOK_BEFORE_TESTS = before_tests

def after_tests(report_dir):
    pass
RUN_HOOK_AFTER_TESTS = after_tests
