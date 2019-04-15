'''
Created on Jun 14, 2017

@author: nicolas
'''

from decimal import Decimal
from functools import reduce

import six

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

from lemoncheesecake.reporting.backend import FileReportBackend
from lemoncheesecake.reporting.report import Log, Check, format_timestamp_as_iso_8601
from lemoncheesecake.consts import LOG_LEVEL_ERROR
from lemoncheesecake.reporting.backends.xml import make_xml_child, make_xml_node, indent_xml, set_node_attr, \
    DEFAULT_INDENT_LEVEL


def format_duration(duration):
    return "%d.%03d" % (int(duration), Decimal(round(duration, 3)) % 1 * 1000)


def _serialize_test_data(test):
    junit_test = make_xml_node(
        "testcase",
        "name", test.name,
        "time", format_duration(test.duration if test.end_time else 0),
    )
    
    if test.status == "skipped":
        make_xml_child(junit_test, "skipped")
    else:
        for step in test.steps:
            for step_entry in step.entries:
                if isinstance(step_entry, Check) and step_entry.outcome is False:
                    make_xml_child(junit_test, "failure", "message", "failed check in step '%s'" % step.description)
                elif isinstance(step_entry, Log) and step_entry.level == LOG_LEVEL_ERROR:
                    make_xml_child(junit_test, "error", "message", "error log in step '%s'" % step.description)

    return junit_test


def _serialize_suite_data(suite):
    junit_testsuites = []
    tests = suite.get_tests()
    if tests:
        junit_testsuite = make_xml_node(
            "testsuite", 
            "name", suite.path,
            "tests", str(len(tests)),
            "failures", str(len(list(filter(lambda t: t.status == "failed", tests)))),
            "skipped", str(len(list(filter(lambda t: t.status == "skipped", tests)))),
            "time", format_duration(reduce(lambda x, y: x + y, (t.duration for t in tests if t.end_time), 0)),
            "timestamp", format_timestamp_as_iso_8601(min(t.start_time for t in tests))
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
    
    report_stats = report.stats()
    set_node_attr(junit_report_testsuites, "tests", str(report_stats.test_statuses["passed"]))
    set_node_attr(junit_report_testsuites, "failures", str(report_stats.test_statuses["failed"]))
    if report.end_time is not None:
        set_node_attr(junit_report_testsuites, "time", format_duration(report.end_time - report.start_time))
    
    for suite in report.get_suites():
        junit_testsuites = _serialize_suite_data(suite)
        for junit_testsuite in junit_testsuites:
            junit_report_testsuites.append(junit_testsuite)

    return junit_report_testsuites


def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    report = serialize_report_as_tree(report)
    indent_xml(report, indent_level=indent_level)

    if six.PY3:
        return ET.tostring(report, pretty_print=True, encoding="unicode")
    else:
        return ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8")


def save_report_into_file(report, filename, indent_level=DEFAULT_INDENT_LEVEL):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)


class JunitBackend(FileReportBackend):
    name = "junit"

    def __init__(self):
        self.indent_level = DEFAULT_INDENT_LEVEL

    def get_report_filename(self):
        return "report-junit.xml"

    def is_available(self):
        return LXML_IS_AVAILABLE

    def save_report(self, filename, report):
        save_report_into_file(report, filename, self.indent_level)
