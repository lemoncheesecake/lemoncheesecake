"""
This module gather public API to be used within suites, this module can be imported
as this for convenience:
import lemoncheesecake.api as lcc
"""

from lemoncheesecake.suite import Test, add_test_into_suite, \
    get_metadata, suite, test, tags, prop, link, disabled, conditional, hidden, depends_on, inject_fixture
from lemoncheesecake.session import set_step, detached_step, end_step, log_debug, log_info, log_warning, log_warn, log_error, \
    log_check, prepare_attachment, prepare_image_attachment, save_attachment_file, save_image_file, \
    save_attachment_content, save_image_content, log_url, get_fixture, add_report_info, Thread
from lemoncheesecake.fixture import fixture
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, UserError

# for pydoc & sphinx
__all__ = dir()
