import os

from lemoncheesecake import loader
from lemoncheesecake.reporting import reportdir

project_dir = os.path.dirname(__file__)
TESTSUITES = loader.import_testsuites_from_directory("suites")
FIXTURES = loader.import_fixtures_from_directory(os.path.join(project_dir, "fixtures"))

def fail(dummy):
    raise Exception("operation has failed")

REPORT_DIR_CREATION = lambda top_dir: reportdir.report_dir_with_archiving(top_dir, reportdir.archive_dirname_datetime)

# Test run hooks
def before_tests(report_dir):
    pass
RUN_HOOK_BEFORE_TESTS = before_tests

def after_tests(report_dir):
    pass
RUN_HOOK_AFTER_TESTS = after_tests
