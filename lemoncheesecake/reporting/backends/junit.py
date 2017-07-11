'''
Created on Jun 14, 2017

@author: nicolas
'''

from decimal import Decimal

# This junit backend implementation is based on the documentation 
# http://llg.cubic.org/docs/junit/
# also see:
# https://confluence.atlassian.com/display/BAMBOO/JUnit+parsing+in+Bamboo

try:
    from lxml import etree as ET
    from lxml.builder import E
    LXML_IS_AVAILABLE = True
except ImportError:
    LXML_IS_AVAILABLE = False

from lemoncheesecake.reporting.backend import FileReportBackend, SAVE_AT_EACH_FAILED_TEST
from lemoncheesecake.reporting.report import LogData, CheckData, format_timestamp_as_iso_8601
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.consts import LOG_LEVEL_ERROR
from lemoncheesecake.reporting.backends.xml import make_xml_child, make_xml_node, indent_xml, set_node_attr, \
    DEFAULT_INDENT_LEVEL

def format_duration(duration):
    return "%d.%03d" % (int(duration), Decimal(round(duration, 3)) % 1 * 1000)

def _serialize_test_data(test):
    junit_test = make_xml_node(
        "testcase",
        "name", test.name,
        "time", format_duration(test.end_time - test.start_time),
    )
    
    if test.status == "skipped":
        make_xml_child(junit_test, "skipped")
    else:
        for step in test.steps:
            for step_entry in step.entries:
                if isinstance(step_entry, CheckData) and step_entry.outcome == False:
                    make_xml_child(junit_test, "failure", "message", "failed check in step '%s'" % step.description)
                elif isinstance(step_entry, LogData) and step_entry.level == LOG_LEVEL_ERROR:
                    make_xml_child(junit_test, "error", "message", "error log in step '%s'" % step.description)

    return junit_test

def _serialize_suite_data(suite):
    junit_testsuites = []
    tests = suite.get_tests()
    if tests:
        junit_testsuite = make_xml_node(
            "testsuite", 
            "name", suite.get_path_as_str(),
            "tests", str(len(tests)),
            "failures", str(len(list(filter(lambda test: test.status == "failed", tests)))),
            "skipped", str(len(list(filter(lambda test: test.status == "skipped", tests)))),
            "time", format_duration(tests[-1].end_time - tests[0].start_time),
            "timestamp", format_timestamp_as_iso_8601(tests[0].start_time)
        )
        junit_testsuites.append(junit_testsuite)
        for test in tests:
            junit_test = _serialize_test_data(test)
            junit_testsuite.append(junit_test)
    
    for sub_suite in suite.get_suites():
        junit_sub_testsuites = _serialize_suite_data(sub_suite)
        for junit_sub_testsuite in junit_sub_testsuites:
            junit_testsuites.append(junit_sub_testsuite)
    
    return junit_testsuites
    
def serialize_report_as_tree(report):
    junit_report_testsuites = E("testsuites")
    
    report_stats = report.get_stats()
    set_node_attr(junit_report_testsuites, "tests", str(report_stats.test_statuses["passed"]))
    set_node_attr(junit_report_testsuites, "failures", str(report_stats.test_statuses["failed"]))
    if report.end_time != None:
        set_node_attr(junit_report_testsuites, "time", format_duration(report.end_time - report.start_time))
    
    for suite in report.suites:
        junit_testsuites = _serialize_suite_data(suite)
        for junit_testsuite in junit_testsuites:
            junit_report_testsuites.append(junit_testsuite)

    return junit_report_testsuites

def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    report = serialize_report_as_tree(report)
    indent_xml(report, indent_level=indent_level)

    if IS_PYTHON3:
        return ET.tostring(report, pretty_print=True, encoding="unicode")
    return ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8")

def save_report_into_file(report, filename, indent_level=DEFAULT_INDENT_LEVEL):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)

class JunitBackend(FileReportBackend):
    name = "junit"

    def __init__(self, save_mode=SAVE_AT_EACH_FAILED_TEST):
        FileReportBackend.__init__(self, save_mode)
        self.indent_level = DEFAULT_INDENT_LEVEL

    def get_report_filename(self):
        return "report-junit.xml"

    def is_available(self):
        return LXML_IS_AVAILABLE

    def save_report(self, filename, report):
        save_report_into_file(report, filename, self.indent_level)
