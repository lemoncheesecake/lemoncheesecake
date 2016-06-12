#!/usr/bin/python

import sys
sys.path.insert(0, ".")

from lemoncheesecake.common import reporting_dir_with_datetime
from lemoncheesecake.loader import load_testsuites_from_directory
from lemoncheesecake.reportingbackends.console import ConsoleBackend
from lemoncheesecake.reportingbackends.xml import XmlBackend
from lemoncheesecake.reportingbackends.json_ import JsonBackend
from lemoncheesecake.reportingbackends.html import HtmlBackend

TESTSUITES = load_testsuites_from_directory("suites")

# Reporting
REPORTING_ROOT_DIR = "reports"
REPORTING_DIR_FORMAT = reporting_dir_with_datetime
REPORTING_BACKENDS = ConsoleBackend(), XmlBackend(), JsonBackend(pretty_formatting=True), HtmlBackend()