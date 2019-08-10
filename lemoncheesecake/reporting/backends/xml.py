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
from lemoncheesecake.reporting.backend import BoundReport, FileReportBackend, ReportUnserializerMixin
from lemoncheesecake.reporting.report import (
    Log, Check, Attachment, Url, Step, Result, TestResult, SuiteResult,
    format_time_as_iso8601, parse_iso8601_time
)
from lemoncheesecake.exceptions import ProgrammingError, InvalidReportFile, IncompatibleReportFile

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


def set_node_attr(node, attr_name, attr_value):
    if six.PY3:
        node.attrib[attr_name] = attr_value
    else:
        node.attrib[attr_name] = attr_value if type(attr_value) is unicode else unicode(attr_value, "utf-8")


def make_xml_node(name, *args):
    node = E(name)
    i = 0
    while i < len(args):
        attr_name, attr_value = args[i], args[i+1]
        if attr_value is not None:
            set_node_attr(node, attr_name, attr_value)
        i += 2
    return node


def make_xml_child(parent_node, name, *args):
    node = make_xml_node(name, *args)
    parent_node.append(node)
    return node


def _add_time_attr(node, name, value):
    if not value:
        return
    node.attrib[name] = format_time_as_iso8601(value)


def _serialize_bool(value):
    return "true" if value else "false"


def _serialize_steps(steps, parent_node):
    for step in steps:
        step_node = make_xml_child(parent_node, "step", "description", step.description)
        _add_time_attr(step_node, "start-time", step.start_time)
        _add_time_attr(step_node, "end-time", step.end_time)
        for entry in step.entries:
            if isinstance(entry, Log):
                log_node = make_xml_child(
                    step_node, "log",
                    "level", entry.level,
                    "time", format_time_as_iso8601(entry.time)
                )
                log_node.text = entry.message
            elif isinstance(entry, Attachment):
                attachment_node = make_xml_child(
                    step_node, "attachment",
                    "description", entry.description,
                    "as-image", _serialize_bool(entry.as_image),
                    "time", format_time_as_iso8601(entry.time)
                )
                attachment_node.text = entry.filename
            elif isinstance(entry, Url):
                url_node = make_xml_child(
                    step_node, "url",
                    "description", entry.description,
                    "time", format_time_as_iso8601(entry.time)
                )
                url_node.text = entry.url
            else:  # TestCheck
                check_node = make_xml_child(
                    step_node, "check",
                    "description", entry.description,
                    "is-successful", _serialize_bool(entry.is_successful),
                    "time", format_time_as_iso8601(entry.time)
                )
                check_node.text = entry.details


def _serialize_test_data(test):
    test_node = make_xml_node(
        "test", "name", test.name, "description", test.description,
        "status", test.status, "status-details", test.status_details
    )
    _add_time_attr(test_node, "start-time", test.start_time)
    _add_time_attr(test_node, "end-time", test.end_time)
    for tag in test.tags:
        tag_node = make_xml_child(test_node, "tag")
        tag_node.text = tag
    for name, value in test.properties.items():
        property_node = make_xml_child(test_node, "property", "name", name)
        property_node.text = value
    for link in test.links:
        link_node = make_xml_child(test_node, "link", "name", link[1])
        link_node.text = link[0]
    _serialize_steps(test.steps, test_node)

    return test_node


def _serialize_hook_data(data, node):
    node.attrib["status"] = data.status or ""
    _add_time_attr(node, "start-time", data.start_time)
    _add_time_attr(node, "end-time", data.end_time)
    _serialize_steps(data.steps, node)


def _serialize_suite_data(suite):
    suite_node = make_xml_node("suite", "name", suite.name, "description", suite.description)
    _add_time_attr(suite_node, "start-time", suite.start_time)
    _add_time_attr(suite_node, "end-time", suite.end_time)
    for tag in suite.tags:
        tag_node = make_xml_child(suite_node, "tag")
        tag_node.text = tag
    for name, value in suite.properties.items():
        property_node = make_xml_child(suite_node, "property", "name", name)
        property_node.text = value
    for link in suite.links:
        link_node = make_xml_child(suite_node, "link", "name", link[1])
        link_node.text = link[0]

    # before suite
    if suite.suite_setup:
        _serialize_hook_data(suite.suite_setup, make_xml_child(suite_node, "suite-setup"))

    # tests
    for test in suite.get_tests():
        test_node = _serialize_test_data(test)
        suite_node.append(test_node)

    # sub suites
    for sub_suite in suite.get_suites():
        sub_suite_node = _serialize_suite_data(sub_suite)
        suite_node.append(sub_suite_node)

    # after suite
    if suite.suite_teardown:
        _serialize_hook_data(suite.suite_teardown, make_xml_child(suite_node, "suite-teardown"))

    return suite_node


def serialize_report_as_tree(report):
    xml = E("lemoncheesecake-report")
    xml.attrib["lemoncheesecake-version"] = lemoncheesecake.__version__
    xml.attrib["report-version"] = "1.0"
    _add_time_attr(xml, "start-time", report.start_time)
    _add_time_attr(xml, "end-time", report.end_time)
    _add_time_attr(xml, "generation-time", time.time())
    xml.attrib["nb-threads"] = str(report.nb_threads)

    title_node = make_xml_child(xml, "title")
    title_node.text = report.title
    for name, value in report.info:
        info_node = make_xml_child(xml, "info", "name", name)
        info_node.text = value

    if report.test_session_setup:
        _serialize_hook_data(report.test_session_setup, make_xml_child(xml, "test-session-setup"))

    for suite in report.get_suites():
        suite_node = _serialize_suite_data(suite)
        xml.append(suite_node)

    if report.test_session_teardown:
        _serialize_hook_data(report.test_session_teardown, make_xml_child(xml, "test-session-teardown"))

    return xml


def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    xml_report = serialize_report_as_tree(report)
    indent_xml(xml_report, indent_level=indent_level)

    if six.PY3:
        return ET.tostring(xml_report, pretty_print=True, encoding="unicode")
    else:
        return ET.tostring(xml_report, pretty_print=True, xml_declaration=True, encoding="utf-8")


def save_report_into_file(report, filename, indent_level=DEFAULT_INDENT_LEVEL):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)


def _unserialize_datetime(value):
    return parse_iso8601_time(value)


def _unserialize_bool(value):
    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        raise ProgrammingError("Invalid boolean representation: '%s'" % value)


def _unserialize_step_data(xml):
    step = Step(xml.attrib["description"])
    step.start_time = _unserialize_datetime(xml.attrib["start-time"])
    step.end_time = _unserialize_datetime(xml.attrib["end-time"]) if "end-time" in xml.attrib else None
    for xml_entry in xml:
        if xml_entry.tag == "log":
            entry = Log(
                xml_entry.attrib["level"], xml_entry.text, _unserialize_datetime(xml_entry.attrib["time"])
            )
        elif xml_entry.tag == "attachment":
            entry = Attachment(
                xml_entry.attrib["description"], xml_entry.text,
                _unserialize_bool(xml_entry.attrib["as-image"]),
                _unserialize_datetime(xml_entry.attrib["time"])
            )
        elif xml_entry.tag == "url":
            entry = Url(
                xml_entry.attrib["description"], xml_entry.text, _unserialize_datetime(xml_entry.attrib["time"])
            )
        elif xml_entry.tag == "check":
            entry = Check(
                xml_entry.attrib["description"], _unserialize_bool(xml_entry.attrib["is-successful"]),
                xml_entry.text, _unserialize_datetime(xml_entry.attrib["time"])
            )
        else:
            raise ProgrammingError("Unknown tag '%s' for step" % xml_entry.tag)
        step.entries.append(entry)
    return step


def _unserialize_test_data(xml):
    test = TestResult(xml.attrib["name"], xml.attrib["description"])
    test.status = xml.attrib.get("status", None)
    test.status_details = xml.attrib.get("status-details", None)
    test.start_time = _unserialize_datetime(xml.attrib["start-time"])
    test.end_time = _unserialize_datetime(xml.attrib["end-time"]) if "end-time" in xml.attrib else None
    test.tags = [node.text for node in xml.xpath("tag")]
    test.properties = {node.attrib["name"]: node.text for node in xml.xpath("property")}
    test.links = [(link.text, link.attrib.get("name", None)) for link in xml.xpath("link")]
    test.steps = [_unserialize_step_data(step) for step in xml.xpath("step")]
    return test


def _unserialize_hook_data(xml):
    data = Result()
    data.status = xml.attrib["status"] or None
    data.start_time = _unserialize_datetime(xml.attrib["start-time"])
    data.end_time = _unserialize_datetime(xml.attrib["end-time"]) if "end-time" in xml.attrib else None
    data.steps = [_unserialize_step_data(step) for step in xml.xpath("step")]
    return data


def _unserialize_suite_data(xml):
    suite = SuiteResult(xml.attrib["name"], xml.attrib["description"])
    suite.start_time = _unserialize_datetime(xml.attrib["start-time"])
    suite.end_time = _unserialize_datetime(xml.attrib["end-time"]) if "end-time" in xml.attrib else None
    suite.tags = [node.text for node in xml.xpath("tag")]
    suite.properties = {node.attrib["name"]: node.text for node in xml.xpath("property")}
    suite.links = [(link.text, link.attrib.get("name", None)) for link in xml.xpath("link")]

    suite_setup = xml.xpath("suite-setup")
    suite_setup = suite_setup[0] if len(suite_setup) > 0 else None
    if suite_setup is not None:
        suite.suite_setup = _unserialize_hook_data(suite_setup)

    for xml_test in xml.xpath("test"):
        test = _unserialize_test_data(xml_test)
        suite.add_test(test)

    suite_teardown = xml.xpath("suite-teardown")
    suite_teardown = suite_teardown[0] if len(suite_teardown) > 0 else None
    if suite_teardown is not None:
        suite.suite_teardown = _unserialize_hook_data(suite_teardown)

    for xml_suite in xml.xpath("suite"):
        sub_suite = _unserialize_suite_data(xml_suite)
        suite.add_suite(sub_suite)

    return suite


def load_report_from_file(filename):
    report = BoundReport()
    try:
        with open(filename, "r") as fh:
            xml = ET.parse(fh)
    except ET.LxmlError as e:
        raise InvalidReportFile(str(e))
    except IOError as e:
        raise e  # re-raise as-is
    try:
        root = xml.getroot().xpath("/lemoncheesecake-report")[0]
    except IndexError:
        raise InvalidReportFile("Cannot find lemoncheesecake-report element in XML")

    report_version = float(root.attrib["report-version"])
    if report_version >= 2.0:
        raise IncompatibleReportFile("Incompatible report version: got %s while 1.x is supported" % report_version)

    report.start_time = _unserialize_datetime(root.attrib["start-time"]) if "start-time" in root.attrib else None
    report.end_time = _unserialize_datetime(root.attrib["end-time"]) if "end-time" in root.attrib else None
    report.report_generation_time = _unserialize_datetime(root.attrib["generation-time"]) if "generation-time" in root.attrib else None
    report.nb_threads = int(root.attrib["nb-threads"])
    report.title = root.xpath("title")[0].text
    report.info = [[node.attrib["name"], node.text] for node in root.xpath("info")]

    test_session_setup = xml.xpath("test-session-setup")
    test_session_setup = test_session_setup[0] if len(test_session_setup) else None
    if test_session_setup is not None:
        report.test_session_setup = _unserialize_hook_data(test_session_setup)

    for xml_suite in root.xpath("suite"):
        suite = _unserialize_suite_data(xml_suite)
        report.add_suite(suite)

    test_session_teardown = xml.xpath("test-session-teardown")
    test_session_teardown = test_session_teardown[0] if len(test_session_teardown) else None
    if test_session_teardown is not None:
        report.test_session_teardown = _unserialize_hook_data(test_session_teardown)

    return report


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

    def load_report(self, filename):
        return load_report_from_file(filename).bind(self, filename)
