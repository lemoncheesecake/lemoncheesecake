'''
Created on Mar 27, 2016

@author: nicolas
'''

from lemoncheesecake.testresults import *
from lemoncheesecake.reporting import ReportingBackend

from lxml import etree as ET
from lxml.builder import E

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

def _serialize_test_result(test):
    test_node = _xml_node("test", "id", test.id, "description", test.description)
    for step in test.steps:
        step_node = _xml_child(test_node, "step", "description", step.description)
        for entry in step.entries:
            if isinstance(entry, TestLog):
                log_node = _xml_child(step_node, "log", "level", entry.level)
                log_node.text = entry.message
            else: # TestCheck
                check_node = _xml_child(step_node, "check", "description", entry.description, "outcome", entry.outcome)
                check_node.details = entry.details
    return test_node

def _serialize_testsuite_result(testsuite):
    testsuite_node = _xml_node("testsuite", "id", testsuite.id, "description", testsuite.description)
    for test in testsuite.tests:
        test_node = _serialize_test_result(test)
        testsuite_node.append(test_node)
    for sub_suite in testsuite.sub_testsuites:
        sub_suite_node = _serialize_testsuite_result(sub_suite)
        testsuite_node.append(sub_suite_node)
    return testsuite_node

def serialize_test_results(results):
    report = E.lemoncheesecake_report()
    for suite in results.testsuites:
        suite_node = _serialize_testsuite_result(suite)
        report.append(suite_node)
    return report

def serialize_test_results_into_file(results, filename):
    report = serialize_test_results(results)
    file = open(filename, "w")
    file.write(ET.tostring(report, pretty_print=True, xml_declaration=True, encoding="utf-8"))
    file.close()

class XmlBackend(ReportingBackend):
    def __init__(self):
        pass
    
    def end_tests(self):
        serialize_test_results_into_file(self.test_results, self.report_dir + "/report.xml")