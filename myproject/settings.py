#!/usr/bin/python

import sys
sys.path.insert(0, ".")

from lemoncheesecake.reportingbackends import html
from lemoncheesecake.common import reporting_dir_with_datetime

from test import *
TESTSUITES = [ MyTestSuite, MyTestSuite1 ]

html.OFFLINE_MODE = True

# Reporting
REPORTING_ROOT_DIR = "reports"
REPORTING_DIR_FORMAT = reporting_dir_with_datetime
REPORTING_BACKENDS = "console", "xml", "json", "html"