import os.path

from lemoncheesecake import loader
from lemoncheesecake.reporting import backend, reportdir
from lemoncheesecake import validators

# Test suites and workers
TESTSUITES = loader.import_testsuites_from_directory(os.path.join(os.path.dirname(__file__), "tests"))
WORKERS = {}
def add_cli_args(cli_parser):
    pass
CLI_EXTRA_ARGS = add_cli_args

# Metadata policy
mp = validators.MetadataPolicy()
METADATA_POLICY = mp

# Reporting
REPORTING_BACKENDS = backend.get_available_backends()
REPORTING_BACKENDS_ACTIVE = "console", "json", "html"
REPORT_DIR_CREATION = lambda top_dir: reportdir.report_dir_with_archiving(top_dir, reportdir.archive_dirname_datetime)

# Test run hooks
def before_tests(report_dir):
    pass
RUN_HOOK_BEFORE_TESTS = before_tests

def after_tests(report_dir):
    pass
RUN_HOOK_AFTER_TESTS = after_tests
