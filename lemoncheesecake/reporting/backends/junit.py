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
from lemoncheesecake.reporting import ReportStats, Log, Check, format_time_as_iso8601
from lemoncheesecake.reporting.backends.xml import make_xml_child, make_xml_node, indent_xml, DEFAULT_INDENT_LEVEL


def _serialization_duration(duration):
    return "%d.%03d" % (int(duration), Decimal(round(duration, 3)) % 1 * 1000)


def _serialize_test_result(test):
    xml_test = make_xml_node(
        "testcase",
        "name", test.name,
        "time", _serialization_duration(test.duration or 0),
    )
    
    if test.status == "skipped":
        make_xml_child(xml_test, "skipped")
    else:
        for step in test.get_steps():
            for log in step.get_logs():
                if isinstance(log, Check) and log.is_successful is False:
                    make_xml_child(xml_test, "failure", "message", "failed check in step '%s'" % step.description)
                elif isinstance(log, Log) and log.level == Log.LEVEL_ERROR:
                    make_xml_child(xml_test, "error", "message", "error log in step '%s'" % step.description)

    return xml_test


def _serialize_suite_result(suite):
    tests = suite.get_tests()
    xml_suite = make_xml_node(
        "testsuite",
        "name", suite.path,
        "tests", str(len(tests)),
        "failures", str(len(list(filter(lambda t: t.status == "failed", tests)))),
        "skipped", str(len(list(filter(lambda t: t.status == "skipped", tests)))),
        "time", _serialization_duration(reduce(lambda x, y: x + y, (t.duration or 0 for t in tests), 0)),
        "timestamp", format_time_as_iso8601(min(t.start_time for t in tests))
    )
    xml_suite.extend(map(_serialize_test_result, tests))
    return xml_suite


def serialize_report_as_xml_tree(report):
    xml_report = E("testsuites")

    stats = ReportStats.from_report(report)

    xml_report.attrib["tests"] = str(stats.tests_nb_by_status["passed"])
    xml_report.attrib["failures"] = str(stats.tests_nb_by_status["failed"])

    if report.end_time is not None:
        xml_report.attrib["time"] = _serialization_duration(report.end_time - report.start_time)

    for suite in report.all_suites():
        if suite.get_tests():
            xml_report.append(_serialize_suite_result(suite))

    return xml_report


def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    xml_report = serialize_report_as_xml_tree(report)
    indent_xml(xml_report, indent_level=indent_level)

    if six.PY3:
        return ET.tostring(xml_report, pretty_print=True, encoding="unicode")
    else:
        return ET.tostring(xml_report, pretty_print=True, xml_declaration=True, encoding="utf-8")


def save_report_into_file(report, filename, indent_level=DEFAULT_INDENT_LEVEL):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)


class JunitBackend(FileReportBackend):
    def __init__(self):
        self.indent_level = DEFAULT_INDENT_LEVEL

    def get_name(self):
        return "junit"

    def is_available(self):
        return LXML_IS_AVAILABLE

    def get_report_filename(self):
        return "report-junit.xml"

    def save_report(self, filename, report):
        save_report_into_file(report, filename, self.indent_level)
