"""
This module gather public API to be used within suites, this module can be imported
as this for convenience:
import lemoncheesecake.api as lcc
"""

from lemoncheesecake.suite import Test, add_test_in_suite, add_tests_in_suite, \
    get_metadata, suite, test, tags, prop, link, disabled, conditional, inject_fixture
from lemoncheesecake.runtime import *
from lemoncheesecake.checkers import *
from lemoncheesecake.matching import *
from lemoncheesecake.fixtures import fixture
from lemoncheesecake.exceptions import AbortTest, AbortSuite, AbortAllTests, UserError

# for pydoc
__all__ = dir()