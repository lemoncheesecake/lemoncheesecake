'''
Created on Mar 27, 2016

@author: nicolas
'''

from lemoncheesecake.reportingdata import *
from lemoncheesecake.reporting import ReportingBackend

from lxml import etree as ET
from lxml.builder import E

OUTCOME_NOT_AVAILABLE = "n/a"
OUTCOME_FAILURE = "failure"
OUTCOME_SUCCESS = "success"

# borrowed from http://stackoverflow.com/a/1239193
def _xml_indent(elem, level=0):
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _xml_indent(elem, level+1)
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
                if entry.outcome == True:
                    outcome = OUTCOME_SUCCESS
                elif entry.outcome == False:
                    outcome = OUTCOME_FAILURE
                else:
                    outcome = OUTCOME_NOT_AVAILABLE
                check_node = _xml_child(step_node, "check", "description", entry.description, "outcome", outcome)
                check_node.text = entry.details

def _serialize_test_data(test):
    test_node = _xml_node("test", "id", test.id, "description", test.description)
    _add_time_attr(test_node, "start-time", test.start_time)
    _add_time_attr(test_node, "end-time", test.end_time)
    for tag in test.tags:
        tag_node = _xml_child(test_node, "tag")
        tag_node.text = tag
    for ticket in test.tickets:
        ticket_node = _xml_child(test_node, "ticket", "id", ticket[0])
        ticket_node.text = ticket[1]
    _serialize_steps(test.steps, test_node)
    
    return test_node

def _serialize_testsuite_data(suite):
    suite_node = _xml_node("suite", "id", suite.id, "description", suite.description)
    for tag in suite.tags:
        tag_node = _xml_child(suite_node, "tag")
        tag_node.text = tag
    for ticket in suite.tickets:
        ticket_node = _xml_child(suite_node, "ticket", "id", ticket[0])
        ticket_node.text = ticket[1]
    
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

def serialize_reporting_data_into_file(data, filename):
    report = serialize_reporting_data(data)
    _xml_indent(report)
    file = open(filename, "w")
    file.write(ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8"))
    file.close()

class XmlBackend(ReportingBackend):
    def __init__(self):
        pass
    
    def end_tests(self):
        serialize_reporting_data_into_file(self.reporting_data, self.report_dir + "/report.xml")