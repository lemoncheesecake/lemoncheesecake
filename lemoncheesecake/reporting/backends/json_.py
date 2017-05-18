'''
Created on Mar 27, 2016

@author: nicolas
'''

import os
import re
import json
from collections import OrderedDict

from lemoncheesecake.reporting.backend import FileReportBackend, SAVE_AT_EACH_FAILED_TEST
from lemoncheesecake.reporting.report import (
    LogData, CheckData, AttachmentData, UrlData, StepData, TestData, HookData, TestSuiteData,
    Report, format_timestamp, parse_timestamp
)
from lemoncheesecake.exceptions import InvalidReportFile

JS_PREFIX = "var reporting_data = "

def _serialize_time(ts):
    return format_timestamp(ts) if ts else None

def _dict(*args):
    d = OrderedDict()
    i = 0
    while i < len(args):
        d[args[i]] = args[i+1]
        i += 2
    return d

def _serialize_steps(steps):
    json_steps = []
    for step in steps:
        json_step = _dict(
            "description", step.description,
            "start_time", _serialize_time(step.start_time),
            "end_time", _serialize_time(step.end_time),
            "entries", []
        )
        json_steps.append(json_step)
        for entry in step.entries:
            if isinstance(entry, LogData):
                entry = _dict("type", "log", "level", entry.level, "message", entry.message, "time", _serialize_time(entry.time))
            elif isinstance(entry, AttachmentData):
                entry = _dict("type", "attachment", "description", entry.description, "filename", entry.filename)
            elif isinstance(entry, UrlData):
                entry = _dict("type", "url", "description", entry.description, "url", entry.url)
            else: # TestCheck
                entry = _dict("type", "check", "description", entry.description, "outcome", entry.outcome, "details", entry.details)
            json_step["entries"].append(entry)
    return json_steps

def _serialize_common_data(obj):
    return _dict(
        "name", obj.name, "description", obj.description,
        "tags", obj.tags,
        "properties", obj.properties,
        "links", [ _dict("name", link[1], "url", link[0]) for link in obj.links ]
    )

def _serialize_test_data(test):
    serialized = _serialize_common_data(test)
    serialized.update(_dict(
        "start_time", _serialize_time(test.start_time),
        "end_time", _serialize_time(test.end_time),
        "steps", _serialize_steps(test.steps),
        "status", test.status,
        "status_details", test.status_details
    ))
    return serialized

def _serialize_hook_data(hook_data):
    return _dict(
        "start_time", _serialize_time(hook_data.start_time),
        "end_time", _serialize_time(hook_data.end_time),
        "steps", _serialize_steps(hook_data.steps),
        "outcome", hook_data.outcome
    )

def _serialize_testsuite_data(suite):
    json_suite = _serialize_common_data(suite)
    json_suite.update(_dict(
        "tests", [ _serialize_test_data(t) for t in suite.tests ],
        "sub_suites", [ _serialize_testsuite_data(s) for s in suite.sub_testsuites ]
    ))
    if suite.suite_setup:
        json_suite["suite_setup"] = _serialize_hook_data(suite.suite_setup)
    if suite.suite_teardown:
        json_suite["suite_teardown"] = _serialize_hook_data(suite.suite_teardown)
    
    return json_suite

def serialize_report_into_json(report):
    serialized = _dict(
        "lemoncheesecake_report_version", 1.0,
        "start_time", _serialize_time(report.start_time),
        "end_time", _serialize_time(report.end_time),
        "generation_time", _serialize_time(report.report_generation_time),
        "info", [ [ n, v ] for n, v in report.info ],
        "stats", [ [ n, v ] for n, v in report.serialize_stats() ]
    )
    
    if report.test_session_setup:
        serialized["test_session_setup"] = _serialize_hook_data(report.test_session_setup)
    
    serialized["suites"] = [ _serialize_testsuite_data(s) for s in report.testsuites ]
    
    if report.test_session_teardown:
        serialized["test_session_teardown"] = _serialize_hook_data(report.test_session_teardown)
    
    return serialized

def save_report_into_file(data, filename, javascript_compatibility=True, pretty_formatting=False):
    report = serialize_report_into_json(data)
    file = open(filename, "w")
    if javascript_compatibility:
        file.write(JS_PREFIX)
    if pretty_formatting:
        file.write(json.dumps(report, indent=4))
    else:
        file.write(json.dumps(report))
    file.close()

def _unserialize_time(t):
    return parse_timestamp(t)

def _unserialize_step_data(js):
    step = StepData(js["description"])
    step.start_time = _unserialize_time(js["start_time"])
    step.end_time = _unserialize_time(js["end_time"])
    for js_entry in js["entries"]:
        if js_entry["type"] == "log":
            entry = LogData(js_entry["level"], js_entry["message"], _unserialize_time(js_entry["time"]))
        elif js_entry["type"] == "attachment":
            entry = AttachmentData(js_entry["description"], js_entry["filename"])
        elif js_entry["type"] == "url":
            entry = UrlData(js_entry["description"], js_entry["url"])
        elif js_entry["type"] == "check":
            entry = CheckData(js_entry["description"], js_entry["outcome"], js_entry["details"])
        step.entries.append(entry)
    return step

def _unserialize_test_data(js):
    test = TestData(js["name"], js["description"])
    test.status = js["status"]
    test.status_details = js["status_details"]
    test.start_time = _unserialize_time(js["start_time"])
    test.end_time = _unserialize_time(js["end_time"])
    test.tags = js["tags"]
    test.properties = js["properties"]
    test.links = [ (link["url"], link["name"]) for link in js["links"] ]
    test.steps = [ _unserialize_step_data(s) for s in js["steps"] ]
    return test

def _unserialize_hook_data(js):
    data = HookData()
    data.outcome = js["outcome"]
    data.start_time = _unserialize_time(js["start_time"])
    data.end_time = _unserialize_time(js["end_time"])
    data.steps = [ _unserialize_step_data(s) for s in js["steps"] ]

    return data

def _unserialize_testsuite_data(js, parent=None):
    suite = TestSuiteData(js["name"], js["description"], parent)
    suite.tags = js["tags"]
    suite.properties = js["properties"]
    suite.links = [ (link["url"], link["name"]) for link in js["links"] ]

    if "suite_setup" in js:
        suite.suite_setup = _unserialize_hook_data(js["suite_setup"])

    suite.tests = [ _unserialize_test_data(t) for t in js["tests"] ]
    
    if "suite_teardown" in js:
        suite.suite_teardown = _unserialize_hook_data(js["suite_teardown"])
    
    suite.sub_testsuites = [ _unserialize_testsuite_data(s, suite) for s in js["sub_suites"] ]
    
    return suite

def load_report_from_file(filename):
    report = Report()
    file = open(filename, "r")
    content = file.read()
    file.close()
    content = re.sub("^" + JS_PREFIX, "", content)
    
    try:
        js = json.loads(content)
    except ValueError as e:
        raise InvalidReportFile(str(e))
    
    if "lemoncheesecake_report_version" not in js:
        raise InvalidReportFile("Cannot find 'lemoncheesecake_report_version' in JSON")
    
    report.info = js["info"]
    report.stats = js["stats"]
    report.start_time = _unserialize_time(js["start_time"])
    report.end_time = _unserialize_time(js["end_time"])
    report.report_generation_time = _unserialize_time(js["generation_time"])
    
    if "test_session_setup" in js:
        report.test_session_setup = _unserialize_hook_data(js["test_session_setup"])
    
    report.testsuites = [ _unserialize_testsuite_data(s) for s in js["suites"] ]
    
    if "test_session_teardown" in js:
        report.test_session_teardown = _unserialize_hook_data(js["test_session_teardown"])
    
    return report

class JsonBackend(FileReportBackend):
    name = "json"
    
    def __init__(self, save_mode=SAVE_AT_EACH_FAILED_TEST, javascript_compatibility=True, pretty_formatting=False):
        FileReportBackend.__init__(self, save_mode)
        self.javascript_compatibility = javascript_compatibility
        self.pretty_formatting = pretty_formatting
    
    def get_report_filename(self):
        return "report.json"
    
    def save_report(self, filename, report):
        save_report_into_file(
            report, filename,
            javascript_compatibility=self.javascript_compatibility, pretty_formatting=self.pretty_formatting
        )
    
    def load_report(self, filename):
        return load_report_from_file(filename)