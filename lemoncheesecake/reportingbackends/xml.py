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

def _serialize_steps_with_log_only(steps, parent_node):
    for step in steps:
        step_node = _xml_child(parent_node, "step", "description", step.description)
        for entry in step.entries:
            log_node = _xml_child(step_node, "log", "level", entry.level)
            log_node.text = entry.message

def _serialize_test_result(test):
    test_node = _xml_node("test", "id", test.id, "description", test.description)
    for step in test.steps:
        step_node = _xml_child(test_node, "step", "description", step.description)
        for entry in step.entries:
            if isinstance(entry, LogData):
                log_node = _xml_child(step_node, "log", "level", entry.level)
                log_node.text = entry.message
            else: # TestCheck
                if entry.outcome == True:
                    outcome = OUTCOME_SUCCESS
                elif entry.outcome == False:
                    outcome = OUTCOME_FAILURE
                else:
                    outcome = OUTCOME_NOT_AVAILABLE
                check_node = _xml_child(step_node, "check", "description", entry.description, "outcome", outcome)
                check_node.text = entry.details
    return test_node

def _serialize_testsuite_result(testsuite):
    testsuite_node = _xml_node("testsuite", "id", testsuite.id, "description", testsuite.description)
    
    # before suite
    before_suite_node = _xml_child(testsuite_node, "before_suite")
    _serialize_steps_with_log_only(testsuite.before_suite_steps, before_suite_node)
    
    # tests
    for test in testsuite.tests:
        test_node = _serialize_test_result(test)
        testsuite_node.append(test_node)
    
    # sub suites
    for sub_suite in testsuite.sub_testsuites:
        sub_suite_node = _serialize_testsuite_result(sub_suite)
        testsuite_node.append(sub_suite_node)
    
    # after suite
    after_suite_node = _xml_child(testsuite_node, "after_suite")
    _serialize_steps_with_log_only(testsuite.after_suite_steps, after_suite_node)
    
    return testsuite_node

def serialize_test_results(results):
    report = E.lemoncheesecake_report()
    for suite in results.testsuites:
        suite_node = _serialize_testsuite_result(suite)
        report.append(suite_node)
    return report

def serialize_test_results_into_file(results, filename):
    report = serialize_test_results(results)
    _xml_indent(report)
    file = open(filename, "w")
    file.write(ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8"))
    file.close()

class XmlBackend(ReportingBackend):
    def __init__(self):
        pass
    
    def end_tests(self):
        serialize_test_results_into_file(self.test_results, self.report_dir + "/report.xml")