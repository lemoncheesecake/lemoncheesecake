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

from lemoncheesecake.reporting.backend import ReportingBackend, FileReportBackend, CAPABILITY_UNSERIALIZE
from lemoncheesecake.reporting.report import *
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.exceptions import ProgrammingError

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
    node.attrib[name] = "%f" % value

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
                log_node.text = entry.message
            elif isinstance(entry, AttachmentData):
                attachment_node = _xml_child(step_node, "attachment", "description", entry.description)
                attachment_node.text = entry.filename
            else: # TestCheck
                check_node = _xml_child(step_node, "check", "description", entry.description,
                                        "outcome", _serialize_outcome(entry.outcome))
                check_node.text = entry.details

def _serialize_test_data(test):
    test_node = _xml_node("test", "id", test.id, "description", test.description,
                          "outcome", _serialize_outcome(test.outcome))
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
    _add_time_attr(node, "start-time", data.start_time)
    _add_time_attr(node, "end-time", data.end_time)
    _serialize_steps(data.steps, node)

def _serialize_testsuite_data(suite):
    suite_node = _xml_node("suite", "id", suite.id, "description", suite.description)
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
    if suite.before_suite:
        _serialize_hook_data(suite.before_suite, _xml_child(suite_node, "before-suite"))
    
    # tests
    for test in suite.tests:
        test_node = _serialize_test_data(test)
        suite_node.append(test_node)
    
    # sub suites
    for sub_suite in suite.sub_testsuites:
        sub_suite_node = _serialize_testsuite_data(sub_suite)
        suite_node.append(sub_suite_node)
    
    # after suite
    if suite.after_suite:
        _serialize_hook_data(suite.after_suite, _xml_child(suite_node, "after-suite"))
    
    return suite_node

def serialize_report_as_tree(report):
    xml = E("lemoncheesecake-report")
    _add_time_attr(xml, "start-time", report.start_time)
    _add_time_attr(xml, "end-time", report.end_time)
    _add_time_attr(xml, "generation-time", report.report_generation_time)
    
    for name, value in report.info:
        info_node = _xml_child(xml, "info", "name", name)
        info_node.text = value
    for name, value in report.serialize_stats():
        stat_node = _xml_child(xml, "stat", "name", name)
        stat_node.text = value

    if report.before_all_tests:
        _serialize_hook_data(report.before_all_tests, _xml_child(xml, "before-all-tests"))

    for suite in report.testsuites:
        suite_node = _serialize_testsuite_data(suite)
        xml.append(suite_node)

    if report.after_all_tests:
        _serialize_hook_data(report.after_all_tests, _xml_child(xml, "after-all-tests"))
    
    return xml

def serialize_report_as_string(report, indent_level=DEFAULT_INDENT_LEVEL):
    report = serialize_report_as_tree(report)
    _xml_indent(report, indent_level=indent_level)
    
    if IS_PYTHON3:
        return ET.tostring(report, pretty_print=True, encoding="unicode")
    return ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8")

def serialize_report_into_file(report, filename, indent_level):
    content = serialize_report_as_string(report, indent_level)
    with open(filename, "w") as fh:
        fh.write(content)

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
    step.start_time = float(xml.attrib["start-time"])
    step.end_time = float(xml.attrib["end-time"])
    for xml_entry in xml:
        if xml_entry.tag == "log":
            entry = LogData(xml_entry.attrib["level"], xml_entry.text)
        elif xml_entry.tag == "attachment":
            entry = AttachmentData(xml_entry.attrib["description"], xml_entry.text)
        elif xml_entry.tag == "check":
            entry = CheckData(xml_entry.attrib["description"], _unserialize_outcome(xml_entry.attrib["outcome"]),
                              xml_entry.text)
        step.entries.append(entry)
    return step

def _unserialize_test_data(xml):
    test = TestData(xml.attrib["id"], xml.attrib["description"])
    test.outcome = _unserialize_outcome(xml.attrib["outcome"])
    test.start_time = float(xml.attrib["start-time"])
    test.end_time = float(xml.attrib["end-time"])
    test.tags = [ node.text for node in xml.xpath("tag") ]
    test.properties = { node.attrib["name"]: node.text for node in xml.xpath("property") }
    test.links = [ (link.text, link.attrib["name"]) for link in xml.xpath("link") ]
    test.steps = [ _unserialize_step_data(s) for s in xml.xpath("step") ]
    return test

def _unserialize_hook_data(xml):
    data = HookData()
    data.start_time = float(xml.attrib["start-time"])
    data.end_time = float(xml.attrib["end-time"])
    data.steps = [ _unserialize_step_data(s) for s in xml.xpath("step") ]
    return data

def _unserialize_testsuite_data(xml, parent=None):
    suite = TestSuiteData(xml.attrib["id"], xml.attrib["description"], parent)
    suite.tags = [ node.text for node in xml.xpath("tag") ]
    suite.properties = { node.attrib["name"]: node.text for node in xml.xpath("property") }
    suite.links = [ (link.text, link.attrib["name"]) for link in xml.xpath("link") ]
    
    before_suite = xml.xpath("before-suite")
    before_suite = before_suite[0] if len(before_suite) > 0 else None
    if before_suite != None:
        suite.before_suite = _unserialize_hook_data(before_suite)
        
    suite.tests = [ _unserialize_test_data(t) for t in xml.xpath("test") ]
    
    after_suite = xml.xpath("after-suite")
    after_suite = after_suite[0] if len(after_suite) > 0 else None
    if after_suite != None:
        suite.after_suite = _unserialize_hook_data(after_suite)
    
    suite.sub_testsuites = [ _unserialize_testsuite_data(s, suite) for s in xml.xpath("suite") ]
    
    return suite

def _unserialize_keyvalue_list(nodes):
    ret = [ ]
    for node in nodes:
        ret.append([node.attrib["name"], node.text])
    return ret

def unserialize_report_from_file(filename):
    report = Report()
    xml = ET.parse(open(filename, "r"))
    root = xml.getroot().xpath("/lemoncheesecake-report")[0]
    report.start_time = float(root.attrib["start-time"]) if "start-time" in root.attrib else None
    report.end_time = float(root.attrib["end-time"]) if "end-time" in root.attrib else None
    report.report_generation_time = float(root.attrib["generation-time"]) if "generation-time" in root.attrib else None
    report.info = _unserialize_keyvalue_list(root.xpath("info"))
    report.stats = _unserialize_keyvalue_list(root.xpath("stat"))
    
    before_all_tests = xml.xpath("before-all-tests")
    before_all_tests = before_all_tests[0] if len(before_all_tests) else None
    if before_all_tests:
        report.before_all_tests = _unserialize_hook_data(before_all_tests)
        
    for xml_suite in root.xpath("suite"):
        report.testsuites.append(_unserialize_testsuite_data(xml_suite))

    after_all_tests = xml.xpath("after-all-tests")
    after_all_tests = after_all_tests[0] if len(after_all_tests) else None
    if after_all_tests:
        report.after_all_tests = _unserialize_hook_data(after_all_tests)
    
    return report

class XmlBackend(FileReportBackend):
    name = "xml"
    
    def __init__(self):
        self.indent_level = DEFAULT_INDENT_LEVEL
    
    def is_available(self):
        return LXML_IS_AVAILABLE
    
    def serialize_report(self, report, report_dir):
        serialize_report_into_file(
            report, os.path.join(report_dir, "report.xml"), self.indent_level
        )
    
    def unserialize_report(self, report_path):
        if os.path.isdir(report_path):
            report_path = os.path.join(report_path, "report.xml")
        return unserialize_report_from_file(report_path)
