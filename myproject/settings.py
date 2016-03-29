#!/usr/bin/python

import sys
sys.path.insert(0, ".")

from lemoncheesecake.common import report_dir_with_datetime

from test import *
TESTSUITES = [ MyTestSuite, MyTestSuite1 ]

# Reporting
REPORTS_ROOT_DIR = "reports"
REPORT_DIR_FORMAT = report_dir_with_datetime
REPORT_BACKENDS = "console", "xml"