'''
Created on Mar 27, 2016

@author: nicolas
'''

import time

try:
    from lxml import etree as ET
    from lxml.builder import E
    LXML_IS_AVAILABLE = True
except ImportError:
    LXML_IS_AVAILABLE = False

import six

import lemoncheesecake
from lemoncheesecake.reporting.backend import FileReportBackend, ReportUnserializerMixin
from lemoncheesecake.reporting.report import (
    Report, Log, Check, Attachment, Url, Step, Result, TestResult, SuiteResult,
    format_time_as_iso8601, parse_iso8601_time
)
from lemoncheesecake.exceptions import ReportLoadingError

DEFAULT_INDENT_LEVEL = 4


# borrowed from http://stackoverflow.com/a/1239193
def indent_xml(elem, level=0, indent_level=DEFAULT_INDENT_LEVEL):
    i = "\n" + level * (" " * indent_level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + (" " * indent_level)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level+1, indent_level)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def make_xml_node(name, *args):
    node = E(name)
    i = 0
    while i < len(args):
        attr_name, attr_value = args[i], args[i+1]
        node.attrib[attr_name] = attr_value
        i += 2
    return node


def make_xml_child(parent, name, *args):
    child = make_xml_node(name, *args)
    parent.append(child)
    return child


def _serialize_time(value):
    return format_time_as_iso8601(value)


def _serialize_bool(value):
    return "true" if value else "false"


def _serialize_steps(steps, xml_result):
    for step in steps:
        xml_step = make_xml_child(
            xml_result, "step",
            "description", step.description,
            "start-time", _serialize_time(step.start_time)
        )
        if step.end_time is not None:
            xml_step.attrib["end-time"] = _serialize_time(step.end_time)
        for log in step.get_logs():
            if isinstance(log, Log):
                xml_log = make_xml_child(
                    xml_step, "log",
                    "level", log.level,
                    "time", _serialize_time(log.time)
                )
                xml_log.text = log.message
            elif isinstance(log, Attachment):
                xml_attachment = make_xml_child(
                    xml_step, "attachment",
                    "description", log.description,
                    "as-image", _serialize_bool(log.as_image),
                    "time", _serialize_time(log.time)
                )
                xml_attachment.text = log.filename
            elif isinstance(log, Url):
                xml_url = make_xml_child(
                    xml_step, "url",
                    "description", log.description,
                    "time", _serialize_time(log.time)
                )
                xml_url.text = log.url
            else:  # TestCheck
                xml_check = make_xml_child(
                    xml_step, "check",
                    "description", log.description,
                    "is-successful", _serialize_bool(log.is_successful),
                    "time", _serialize_time(log.time)
                )
                xml_check.text = log.details


def _serialize_result(result, xml_result):
    if result.status:
        xml_result.attrib["status"] = result.status
    if result.status_details:
        xml_result.attrib["status-details"] = result.status_details
    xml_result.attrib["start-time"] = _serialize_time(result.start_time)
    if result.end_time is not None:
        xml_result.attrib["end-time"] = _serialize_time(result.end_time)
    _serialize_steps(result.get_steps(), xml_result)


def _serialize_node_metadata(obj, xml_node):
    xml_node.attrib["name"] = obj.name
    xml_node.attrib["description"] = obj.description

    for tag in obj.tags:
        xml_tag = make_xml_child(xml_node, "tag")
        xml_tag.text = tag
    for name, value in obj.properties.items():
        xml_property = make_xml_child(xml_node, "property", "name", name)
        xml_property.text = value
    for link in obj.links:
        xml_link = make_xml_child(xml_node, "link")
        if link[1]:
            xml_link.attrib["name"] = link[1]
        xml_link.text = link[0]


def _serialize_test_result(test):
    xml_test = make_xml_node("test")
    _serialize_node_metadata(test, xml_test)
    _serialize_result(test, xml_test)
    return xml_test


def _serialize_suite_result(suite):
    xml_suite = make_xml_node("suite")

    _serialize_node_metadata(suite, xml_suite)

    xml_suite.attrib["start-time"] = _serialize_time(suite.start_time)
    if suite.end_time is not None:
        xml_suite.attrib["end-time"] = _serialize_time(suite.end_time)

    # before suite
    if suite.suite_setup:
        _serialize_result(suite.suite_setup, make_xml_child(xml_suite, "suite-setup"))

    # tests
    xml_suite.extend(map(_serialize_test_result, suite.get_tests()))

    # sub suites
    xml_suite.extend(map(_serialize_suite_result, suite.get_suites()))

    # after suite
    if suite.suite_teardown:
        _serialize_result(suite.suite_teardown, make_xml_child(xml_suite, "suite-teardown"))

    return xml_suite


def serialize_report_as_xml_tree(report):
    xml_report = E("lemoncheesecake-report")
    xml_report.attrib["lemoncheesecake-version"] = lemoncheesecake.__version__
    xml_report.attrib["report-version"] = "1.1"
    xml_report.attrib["start-time"] = _serialize_time(report.start_time)
    if report.end_time is not None:
        xml_report.attrib["end-time"] = _serialize_time(report.end_time)
    xml_report.attrib["generation-time"] = _serialize_time(time.time())
    xml_report.attrib["nb-threads"] = str(report.nb_threads)

    xml_title = make_xml_child(xml_report, "title")
    xml_title.text = report.title
    for name, value in report.info:
        xml_info = make_xml_child(xml_report, "info", "name", name)
        xml_info.text = value

    if report.test_session_setup:
        _serialize_result(report.test_session_setup, make_xml_child(xml_report, "test-session-setup"))

    xml_report.extend(map(_serialize_suite_result, report.get_suites()))

    if report.test_session_teardown:
        _serialize_result(report.test_session_teardown, make_xml_child(xml_report, "test-session-teardown"))

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


def _unserialize_time(value):
    return parse_iso8601_time(value)


def _unserialize_bool(value):
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        raise ValueError("Invalid boolean representation: '%s'" % value)


def _unserialize_step(xml_step):
    step = Step(xml_step.attrib["description"])
    step.start_time = _unserialize_time(xml_step.attrib["start-time"])
    step.end_time = _unserialize_time(xml_step.attrib["end-time"]) if "end-time" in xml_step.attrib else None
    for xml_log in xml_step:
        if xml_log.tag == "log":
            step_log = Log(
                xml_log.attrib["level"], xml_log.text, _unserialize_time(xml_log.attrib["time"])
            )
        elif xml_log.tag == "attachment":
            step_log = Attachment(
                xml_log.attrib["description"], xml_log.text,
                _unserialize_bool(xml_log.attrib["as-image"]),
                _unserialize_time(xml_log.attrib["time"])
            )
        elif xml_log.tag == "url":
            step_log = Url(
                xml_log.attrib["description"], xml_log.text, _unserialize_time(xml_log.attrib["time"])
            )
        elif xml_log.tag == "check":
            step_log = Check(
                xml_log.attrib["description"], _unserialize_bool(xml_log.attrib["is-successful"]),
                xml_log.text, _unserialize_time(xml_log.attrib["time"])
            )
        else:
            raise ValueError("Unknown tag '%s' for step" % xml_log.tag)
        step.add_log(step_log)
    return step


def _unserialize_result(xml_result, result):
    result.status = xml_result.attrib.get("status", None)
    # status_details for non-test results has been introduced in report version 1.1:
    result.status_details = xml_result.attrib.get("status-details", None)
    result.start_time = _unserialize_time(xml_result.attrib["start-time"])
    result.end_time = _unserialize_time(xml_result.attrib["end-time"]) if "end-time" in xml_result.attrib else None
    for xml_step in xml_result.xpath("step"):
        result.add_step(_unserialize_step(xml_step))


def _unserialize_node_metadata(xml_node, node):
    node.tags = [n.text for n in xml_node.xpath("tag")]
    node.properties = {n.attrib["name"]: n.text for n in xml_node.xpath("property")}
    node.links = [(n.text, n.attrib.get("name", None)) for n in xml_node.xpath("link")]


def _unserialize_test_result(xml_result):
    test = TestResult(xml_result.attrib["name"], xml_result.attrib["description"])
    _unserialize_result(xml_result, test)
    _unserialize_node_metadata(xml_result, test)
    return test


def _unserialize_suite_result(xml_suite):
    suite = SuiteResult(xml_suite.attrib["name"], xml_suite.attrib["description"])
    suite.start_time = _unserialize_time(xml_suite.attrib["start-time"])
    suite.end_time = _unserialize_time(xml_suite.attrib["end-time"]) if "end-time" in xml_suite.attrib else None
    _unserialize_node_metadata(xml_suite, suite)

    xml_setup = xml_suite.xpath("suite-setup")
    xml_setup = xml_setup[0] if len(xml_setup) > 0 else None
    if xml_setup is not None:
        suite.suite_setup = Result()
        _unserialize_result(xml_setup, suite.suite_setup)

    for xml_test in xml_suite.xpath("test"):
        suite.add_test(_unserialize_test_result(xml_test))

    xml_teardown = xml_suite.xpath("suite-teardown")
    xml_teardown = xml_teardown[0] if len(xml_teardown) > 0 else None
    if xml_teardown is not None:
        suite.suite_teardown = Result()
        _unserialize_result(xml_teardown, suite.suite_teardown)

    for xml_suite in xml_suite.xpath("suite"):
        suite.add_suite(_unserialize_suite_result(xml_suite))

    return suite


def _unserialize_report(xml_report):
    report = Report()

    report.start_time = _unserialize_time(xml_report.attrib["start-time"])
    report.end_time = _unserialize_time(xml_report.attrib["end-time"]) if "end-time" in xml_report.attrib else None
    report.saving_time = _unserialize_time(xml_report.attrib["generation-time"]) if "generation-time" in xml_report.attrib else None
    report.nb_threads = int(xml_report.attrib["nb-threads"])
    report.title = xml_report.xpath("title")[0].text
    report.info = [(node.attrib["name"], node.text) for node in xml_report.xpath("info")]

    xml_setup = xml_report.xpath("test-session-setup")
    xml_setup = xml_setup[0] if len(xml_setup) else None
    if xml_setup is not None:
        report.test_session_setup = Result()
        _unserialize_result(xml_setup, report.test_session_setup)

    for xml_suite in xml_report.xpath("suite"):
        report.add_suite(_unserialize_suite_result(xml_suite))

    xml_teardown = xml_report.xpath("test-session-teardown")
    xml_teardown = xml_teardown[0] if len(xml_teardown) else None
    if xml_teardown is not None:
        report.test_session_teardown = Result()
        _unserialize_result(xml_teardown, report.test_session_teardown)

    return report


def load_report_from_file(filename):
    try:
        with open(filename, "r") as fh:
            xml = ET.parse(fh)
    except ET.LxmlError as e:
        raise ReportLoadingError(str(e))
    except IOError as e:
        raise e  # re-raise as-is
    try:
        root = xml.getroot().xpath("/lemoncheesecake-report")[0]
    except IndexError:
        raise ReportLoadingError("Cannot find lemoncheesecake-report element in XML")

    report_version = float(root.attrib["report-version"])
    if report_version >= 2.0:
        raise ReportLoadingError("Incompatible report version: got %s while 1.x is supported" % report_version)

    return _unserialize_report(root)


class XmlBackend(FileReportBackend, ReportUnserializerMixin):
    def __init__(self):
        self.indent_level = DEFAULT_INDENT_LEVEL

    def get_name(self):
        return "xml"

    def is_available(self):
        return LXML_IS_AVAILABLE

    def get_report_filename(self):
        return "report.xml"

    def save_report(self, filename, report):
        save_report_into_file(report, filename, self.indent_level)

    def load_report(self, path):
        report = load_report_from_file(path)
        report.bind(self, path)
        return report
