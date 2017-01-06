import os.path

from lemoncheesecake import loader
from lemoncheesecake.reporting import backend, backends, reportdir
from lemoncheesecake import validators

# Variables
project_dir = os.path.dirname(__file__)

# Test suites and workers
TESTSUITES = loader.import_testsuites_from_directory(os.path.join(project_dir, "tests"))
WORKERS = {}
def add_cli_args(cli_parser):
    pass
CLI_EXTRA_ARGS = add_cli_args

# Metadata policy
mp = validators.MetadataPolicy()
METADATA_POLICY = mp

# Reporting
console_backend = backends.ConsoleBackend()
json_backend = backends.JsonBackend()
xml_backend = backends.XmlBackend()
html_backend = backends.HtmlBackend()

REPORTING_BACKENDS = console_backend, json_backend, xml_backend, html_backend
REPORTING_BACKENDS_ACTIVE = console_backend.name, json_backend.name, xml_backend.name
REPORT_DIR_CREATION = lambda top_dir: reportdir.report_dir_with_archiving(top_dir, reportdir.archive_dirname_datetime)

# Test run hooks
def before_tests(report_dir):
    pass
RUN_HOOK_BEFORE_TESTS = before_tests

def after_tests(report_dir):
    pass
RUN_HOOK_AFTER_TESTS = after_tests
