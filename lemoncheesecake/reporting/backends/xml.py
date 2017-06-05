'''
Created on Mar 27, 2016

@author: nicolas
'''

import sys
import os.path

try:
    from lxml import etree as ET
    from lxml.builder import E
    LXML_IS_AVAILABLE = True
except ImportError:
    LXML_IS_AVAILABLE = False

from lemoncheesecake.reporting.backend import FileReportBackend, SAVE_AT_EACH_FAILED_TEST
from lemoncheesecake.reporting.report import (
    LogData, CheckData, AttachmentData, UrlData, StepData, TestData, HookData, TestSuiteData,
    Report, format_timestamp, parse_timestamp
)
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.exceptions import ProgrammingError, InvalidReportFile

OUTCOME_NOT_AVAILABLE = "n/a"
OUTCOME_FAILURE = "failure"
OUTCOME_SUCCESS = "success"

DEFAULT_INDENT_LEVEL = 4

# borrowed from http://stackoverflow.com/a/1239193
def _xml_indent(elem, level=0, indent_level=DEFAULT_INDENT_LEVEL):
    i = "\n" + level * (" " * indent_level)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + (" " * indent_level)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _xml_indent(elem, level+1, indent_level)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def _xml_node(name, *args):
    node = E(name)
    i = 0
    while i < len(args):
        name, value = args[i], args[i+1]
        if value is not None:
            if IS_PYTHON3:
                node.attrib[name] = value
            else:
                node.attrib[name] = value if type(value) is unicode else unicode(value, "utf-8")
        i += 2
    return node 

def _xml_child(parent_node, name, *args):
    node = _xml_node(name, *args)
    parent_node.append(node)
    return node

def _add_time_attr(node, name, value):
    if not value:
        return
    node.attrib[name] = format_timestamp(value)

def _serialize_outcome(outcome):
    if outcome == True:
        return OUTCOME_SUCCESS
    if outcome == False:
        return OUTCOME_FAILURE
    return OUTCOME_NOT_AVAILABLE

def _serialize_steps(steps, parent_node):
    for step in steps:
        step_node = _xml_child(parent_node, "step", "description", step.description)
        _add_time_attr(step_node, "start-time", step.start_time)
        _add_time_attr(step_node, "end-time", step.end_time)
        for entry in step.entries:
            if isinstance(entry, LogData):
                log_node = _xml_child(step_node, "log", "level", entry.level)
                _add_time_attr(log_node, "time", entry.time)
                log_node.text = entry.message
            elif isinstance(entry, AttachmentData):
                attachment_node = _xml_child(step_node, "attachment", "description", entry.description)
                attachment_node.text = entry.filename
            elif isinstance(entry, UrlData):
                url_node = _xml_child(step_node, "url", "description", entry.description)
                url_node.text = entry.url
            else: # TestCheck
                check_node = _xml_child(step_node, "check", "description", entry.description,
                                        "outcome", _serialize_outcome(entry.outcome))
                check_node.text = entry.details

def _serialize_test_data(test):
    test_node = _xml_node("test", "name", test.name, "description", test.description,
                          "status", test.status, "status-details", test.status_details)
    _add_time_attr(test_node, "start-time", test.start_time)
    _add_time_attr(test_node, "end-time", test.end_time)
    for tag in test.tags:
        tag_node = _xml_child(test_node, "tag")
        tag_node.text = tag
    for name, value in test.properties.items():
        property_node = _xml_child(test_node, "property", "name", name)
        property_node.text = value
    for link in test.links:
        link_node = _xml_child(test_node, "link", "name", link[1])
        link_node.text = link[0]
    _serialize_steps(test.steps, test_node)
    
    return test_node

def _serialize_hook_data(data, node):
    node.attrib["outcome"] = _serialize_outcome(data.outcome)
    _add_time_attr(node, "start-time", data.start_time)
    _add_time_attr(node, "end-time", data.end_time)
    _serialize_steps(data.steps, node)

def _serialize_testsuite_data(suite):
    suite_node = _xml_node("suite", "name", suite.name, "description", suite.description)
    for tag in suite.tags:
        tag_node = _xml_child(suite_node, "tag")
        tag_node.text = tag
    for name, value in suite.properties.items():
        property_node = _xml_child(suite_node, "property", "name", name)
        property_node.text = value
    for link in suite.links:
        link_node = _xml_child(suite_node, "link", "name", link[1])
        link_node.text = link[0]
    
    # before suite
    if suite.suite_setup:
        _serialize_hook_data(suite.suite_setup, _xml_child(suite_node, "suite-setup"))
    
    # tests
    for test in suite.tests:
        test_node = _serialize_test_data(test)
        suite_node.append(test_node)
    
    # sub suites
    for sub_suite in suite.sub_testsuites:
        sub_suite_node = _serialize_testsuite_data(sub_suite)
        suite_node.append(sub_suite_node)
    
    # after suite
    if suite.suite_teardown:
        _serialize_hook_data(suite.suite_teardown, _xml_child(suite_node, "suite-teardown"))
    
    return suite_node

def serialize_report_as_tree(report):
    xml = E("lemoncheesecake-report")
    version_node = _xml_child(xml, "lemoncheesecake-report-version")
    version_node.text = str("1.0")
    _add_time_attr(xml, "start-time", report.start_time)
    _add_time_attr(xml, "end-time", report.end_time)
    _add_time_attr(xml, "generation-time", report.report_generation_time)
    
    for name, value in report.info:
        info_node = _xml_child(xml, "info", "name", name)
        info_node.text = value
    for name, value in report.serialize_stats():
        stat_node = _xml_child(xml, "stat", "name", name)
        stat_node.text = value

    if report.test_session_setup:
        _serialize_hook_data(report.test_session_setup, _xml_child(xml, "test-session-setup"))

    for suite in report.testsuites:
        suite_node = _serialize_testsuite_data(suite)
        xml.append(suite_node)

    if report.test_session_teardown:
        _serialize_hook_data(report.test_session_teardown, _xml_child(xml, "test-session-teardown"))
    
    return xml

def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    report = serialize_report_as_tree(report)
    _xml_indent(report, indent_level=indent_level)
    
    if IS_PYTHON3:
        return ET.tostring(report, pretty_print=True, encoding="unicode")
    return ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8")

def save_report_into_file(report, filename, indent_level=DEFAULT_INDENT_LEVEL):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)

def _unserialize_datetime(value):
    return parse_timestamp(value)

def _unserialize_outcome(value):
    if value == OUTCOME_SUCCESS:
        return True
    if value == OUTCOME_FAILURE:
        return False
    if value == OUTCOME_NOT_AVAILABLE:
        return None
    raise ProgrammingError("Unknown value '%s' for outcome" % value)

def _unserialize_step_data(xml):
    step = StepData(xml.attrib["description"])
    step.start_time = _unserialize_datetime(xml.attrib["start-time"])
    step.end_time = _unserialize_datetime(xml.attrib["end-time"])
    for xml_entry in xml:
        if xml_entry.tag == "log":
            entry = LogData(xml_entry.attrib["level"], xml_entry.text, _unserialize_datetime(xml_entry.attrib["time"]))
        elif xml_entry.tag == "attachment":
            entry = AttachmentData(xml_entry.attrib["description"], xml_entry.text)
        elif xml_entry.tag == "url":
            entry = UrlData(xml_entry.attrib["description"], xml_entry.text)
        elif xml_entry.tag == "check":
            entry = CheckData(xml_entry.attrib["description"], _unserialize_outcome(xml_entry.attrib["outcome"]),
                              xml_entry.text)
        step.entries.append(entry)
    return step

def _unserialize_test_data(xml):
    test = TestData(xml.attrib["name"], xml.attrib["description"])
    test.status = xml.attrib["status"]
    test.status_details = xml.attrib.get("status-details", None)
    test.start_time = _unserialize_datetime(xml.attrib["start-time"])
    test.end_time = _unserialize_datetime(xml.attrib["end-time"])
    test.tags = [ node.text for node in xml.xpath("tag") ]
    test.properties = { node.attrib["name"]: node.text for node in xml.xpath("property") }
    test.links = [ (link.text, link.attrib["name"]) for link in xml.xpath("link") ]
    test.steps = [ _unserialize_step_data(s) for s in xml.xpath("step") ]
    return test

def _unserialize_hook_data(xml):
    data = HookData()
    data.outcome = _unserialize_outcome(xml.attrib["outcome"])
    data.start_time = _unserialize_datetime(xml.attrib["start-time"])
    data.end_time = _unserialize_datetime(xml.attrib["end-time"])
    data.steps = [ _unserialize_step_data(s) for s in xml.xpath("step") ]
    return data

def _unserialize_testsuite_data(xml, parent=None):
    suite = TestSuiteData(xml.attrib["name"], xml.attrib["description"], parent)
    suite.tags = [ node.text for node in xml.xpath("tag") ]
    suite.properties = { node.attrib["name"]: node.text for node in xml.xpath("property") }
    suite.links = [ (link.text, link.attrib["name"]) for link in xml.xpath("link") ]
    
    suite_setup = xml.xpath("suite-setup")
    suite_setup = suite_setup[0] if len(suite_setup) > 0 else None
    if suite_setup != None:
        suite.suite_setup = _unserialize_hook_data(suite_setup)
        
    suite.tests = [ _unserialize_test_data(t) for t in xml.xpath("test") ]
    
    suite_teardown = xml.xpath("suite-teardown")
    suite_teardown = suite_teardown[0] if len(suite_teardown) > 0 else None
    if suite_teardown != None:
        suite.suite_teardown = _unserialize_hook_data(suite_teardown)
    
    suite.sub_testsuites = [ _unserialize_testsuite_data(s, suite) for s in xml.xpath("suite") ]
    
    return suite

def _unserialize_keyvalue_list(nodes):
    ret = [ ]
    for node in nodes:
        ret.append([node.attrib["name"], node.text])
    return ret

def load_report_from_file(filename):
    report = Report()
    try:
        with open(filename, "r") as fh:
            xml = ET.parse(fh)
    except ET.LxmlError as e:
        raise InvalidReportFile(str(e))
    try:
        root = xml.getroot().xpath("/lemoncheesecake-report")[0]
    except IndexError:
        raise InvalidReportFile("Cannot lemoncheesecake-report element in XML")
    
    report.start_time = _unserialize_datetime(root.attrib["start-time"]) if "start-time" in root.attrib else None
    report.end_time = _unserialize_datetime(root.attrib["end-time"]) if "end-time" in root.attrib else None
    report.report_generation_time = _unserialize_datetime(root.attrib["generation-time"]) if "generation-time" in root.attrib else None
    report.info = _unserialize_keyvalue_list(root.xpath("info"))
    report.stats = _unserialize_keyvalue_list(root.xpath("stat"))
    
    test_session_setup = xml.xpath("test-session-setup")
    test_session_setup = test_session_setup[0] if len(test_session_setup) else None
    if test_session_setup != None:
        report.test_session_setup = _unserialize_hook_data(test_session_setup)
        
    for xml_suite in root.xpath("suite"):
        report.testsuites.append(_unserialize_testsuite_data(xml_suite))

    test_session_teardown = xml.xpath("test-session-teardown")
    test_session_teardown = test_session_teardown[0] if len(test_session_teardown) else None
    if test_session_teardown != None:
        report.test_session_teardown = _unserialize_hook_data(test_session_teardown)
    
    return report

class XmlBackend(FileReportBackend):
    name = "xml"
    
    def __init__(self, save_mode=SAVE_AT_EACH_FAILED_TEST):
        FileReportBackend.__init__(self, save_mode)
        self.indent_level = DEFAULT_INDENT_LEVEL
    
    def get_report_filename(self):
        return "report.xml"
    
    def is_available(self):
        return LXML_IS_AVAILABLE
    
    def save_report(self, filename, report):
        save_report_into_file(report, filename, self.indent_level)
    
    def load_report(self, filename):
        return load_report_from_file(filename)
