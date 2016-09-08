'''
Created on Mar 27, 2016

@author: nicolas
'''

from lemoncheesecake.reportingdata import *
from lemoncheesecake.reporting import ReportingBackend
from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.exceptions import ProgrammingError

from lxml import etree as ET
from lxml.builder import E

OUTCOME_NOT_AVAILABLE = "n/a"
OUTCOME_FAILURE = "failure"
OUTCOME_SUCCESS = "success"

# borrowed from http://stackoverflow.com/a/1239193
def _xml_indent(elem, level=0, indent_level=4):
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
    node.attrib[name] = "%.3f" % value

def _serialize_outcome(outcome):
    if outcome == True:
        return OUTCOME_SUCCESS
    if outcome == False:
        return OUTCOME_FAILURE
    return OUTCOME_NOT_AVAILABLE

def _serialize_steps(steps, parent_node):
    for step in steps:
        step_node = _xml_child(parent_node, "step", "description", step.description)
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
    for url in test.urls:
        url_node = _xml_child(test_node, "url", "name", url[1])
        url_node.text = url[0]
    _serialize_steps(test.steps, test_node)
    
    return test_node

def _serialize_testsuite_data(suite):
    suite_node = _xml_node("suite", "id", suite.id, "description", suite.description)
    for tag in suite.tags:
        tag_node = _xml_child(suite_node, "tag")
        tag_node.text = tag
    for name, value in suite.properties.items():
        property_node = _xml_child(suite_node, "property", "name", name)
        property_node.text = value
    for url in suite.urls:
        url_node = _xml_child(suite_node, "url", "name", url[1])
        url_node.text = url[0]
    
    # before suite
    if suite.before_suite_steps:
        before_suite_node = _xml_child(suite_node, "before-suite")
        _add_time_attr(before_suite_node, "start-time", suite.before_suite_start_time)
        _add_time_attr(before_suite_node, "end-time", suite.before_suite_end_time)
        _serialize_steps(suite.before_suite_steps, before_suite_node)
    
    # tests
    for test in suite.tests:
        test_node = _serialize_test_data(test)
        suite_node.append(test_node)
    
    # sub suites
    for sub_suite in suite.sub_testsuites:
        sub_suite_node = _serialize_testsuite_data(sub_suite)
        suite_node.append(sub_suite_node)
    
    # after suite
    if suite.before_suite_steps:
        after_suite_node = _xml_child(suite_node, "after-suite")
        _add_time_attr(after_suite_node, "start-time", suite.after_suite_start_time)
        _add_time_attr(after_suite_node, "end-time", suite.after_suite_end_time)
        _serialize_steps(suite.after_suite_steps, after_suite_node)
    
    return suite_node

def serialize_reporting_data(data):
    report = E("lemoncheesecake-report")
    _add_time_attr(report, "start-time", data.start_time)
    _add_time_attr(report, "end-time", data.end_time)
    _add_time_attr(report, "generation-time", data.report_generation_time)
    for name, value in data.info:
        info_node = _xml_child(report, "info", "name", name)
        info_node.text = value
    for name, value in data.stats:
        stat_node = _xml_child(report, "stat", "name", name)
        stat_node.text = value
    for suite in data.testsuites:
        suite_node = _serialize_testsuite_data(suite)
        report.append(suite_node)
    return report

def serialize_reporting_data_into_file(data, filename, indent_level):
    report = serialize_reporting_data(data)
    _xml_indent(report, indent_level=indent_level)
    file = open(filename, "w")
    if IS_PYTHON3:
        content = ET.tostring(report, pretty_print=True, encoding="unicode")
    else:
        content = ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8")
    file.write(content)
    file.close()

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
    test.properties = { node.attrib["name"]: node.text for node in xml.xpath("properties") }
    test.urls = [ [u.attrib["name"], u.text] for u in xml.xpath("url") ]
    test.steps = [ _unserialize_step_data(s) for s in xml.xpath("step") ]
    return test

def _unserialize_testsuite_data(xml, parent=None):
    suite = TestSuiteData(xml.attrib["id"], xml.attrib["description"], parent)
    suite.tags = [ node.text for node in xml.xpath("tag") ]
    suite.properties = { node.attrib["name"]: node.text for node in xml.xpath("properties") }
    suite.urls = [ [t.attrib["name"], t.text] for t in xml.xpath("url") ]
    
    before_suite = xml.xpath("before-suite")
    before_suite = before_suite[0] if len(before_suite) > 0 else None
    if before_suite != None:
        suite.before_suite_start_time = float(before_suite.attrib["start-time"])
        suite.before_suite_end_time = float(before_suite.attrib["end-time"])
        suite.before_suite_steps = [ _unserialize_step_data(s) for s in before_suite.xpath("step") ]
        
    suite.tests = [ _unserialize_test_data(t) for t in xml.xpath("test") ]
    
    after_suite = xml.xpath("after-suite")
    after_suite = after_suite[0] if len(after_suite) > 0 else None
    if after_suite != None:
        suite.after_suite_start_time = float(after_suite.attrib["start-time"])
        suite.after_suite_end_time = float(after_suite.attrib["end-time"])
        suite.after_suite_steps = [ _unserialize_step_data(s) for s in after_suite.xpath("step") ]
    
    suite.sub_testsuites = [ _unserialize_testsuite_data(s, suite) for s in xml.xpath("suite") ]
    
    return suite

def _unserialize_keyvalue_list(nodes):
    ret = [ ]
    for node in nodes:
        ret.append([node.attrib["name"], node.text])
    return ret

def unserialize_reporting_data_from_file(filename):
    data = ReportingData()
    xml = ET.parse(open(filename, "r"))
    root = xml.getroot().xpath("/lemoncheesecake-report")[0]
    data.start_time = float(root.attrib["start-time"]) if "start-time" in root.attrib else None
    data.end_time = float(root.attrib["end-time"]) if "end-time" in root.attrib else None
    data.report_generation_time = float(root.attrib["generation-time"]) if "generation-time" in root.attrib else None
    data.info = _unserialize_keyvalue_list(root.xpath("info"))
    data.stats = _unserialize_keyvalue_list(root.xpath("stat"))
    
    for xml_suite in root.xpath("suite"):
        data.testsuites.append(_unserialize_testsuite_data(xml_suite))
    
    return data
    
class XmlBackend(ReportingBackend):
    name = "xml"
    
    def __init__(self):
        self.indent_level = 4
    
    def end_tests(self):
        serialize_reporting_data_into_file(
            self.reporting_data, self.report_dir + "/report.xml", self.indent_level
        )