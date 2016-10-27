'''
Created on Mar 27, 2016

@author: nicolas
'''

import re
import json

from lemoncheesecake.reportingdata import *
from lemoncheesecake.reporting import ReportingBackend

JS_PREFIX = "var reporting_data = "

def _time_value(value):
    return "%.3f" % value if value else None

def _serialize_steps(steps):
    json_steps = []
    for step in steps:
        json_step = { "description": step.description, "entries": [ ] }
        json_steps.append(json_step)
        for entry in step.entries:
            if isinstance(entry, LogData):
                entry = { "type": "log", "level": entry.level, "message": entry.message }
            elif isinstance(entry, AttachmentData):
                entry = { "type": "attachment", "description": entry.description, "filename": entry.filename }
            else: # TestCheck
                entry = { "type": "check", "description": entry.description, "outcome": entry.outcome, "details": entry.details }
            json_step["entries"].append(entry)
    return json_steps

def _serialize_common_data(obj):
    return { 
        "id": obj.id, "description": obj.description,
        "tags": obj.tags,
        "properties": obj.properties,
        "links": [ { "name": link[1], "url": link[0] } for link in obj.links ]
    }

def _serialize_test_data(test):
    serialized = _serialize_common_data(test)
    serialized.update({
        "start_time": _time_value(test.start_time),
        "end_time": _time_value(test.end_time),
        "steps": _serialize_steps(test.steps),
        "outcome": test.outcome
        
    })
    return serialized

def _serialize_testsuite_data(suite):
    json_suite = _serialize_common_data(suite)
    json_suite.update({
        "tests": [ _serialize_test_data(t) for t in suite.tests ],
        "sub_suites": [ _serialize_testsuite_data(s) for s in suite.sub_testsuites ]
    })
    if suite.before_suite_steps:
        json_suite["before_suite"] = {
            "start_time": _time_value(suite.before_suite_start_time),
            "end_time": _time_value(suite.before_suite_end_time),
            "steps": _serialize_steps(suite.before_suite_steps)
        }
    if suite.after_suite_steps:
        json_suite["after_suite"] = {
            "start_time": _time_value(suite.after_suite_start_time),
            "end_time": _time_value(suite.after_suite_end_time),
            "steps": _serialize_steps(suite.after_suite_steps)
        }
    
    return json_suite

def serialize_reporting_data(data):
    return {
        "start_time": _time_value(data.start_time),
        "end_time": _time_value(data.end_time),
        "generation_time": _time_value(data.report_generation_time),
        "suites": [ _serialize_testsuite_data(s) for s in data.testsuites ],
        "info": [ [ n, v ] for n, v in data.info ],
        "stats": [ [ n, v ] for n, v in data.stats ],
    }

def serialize_reporting_data_into_file(data, filename, javascript_compatibility=True, pretty_formatting=False):
    report = serialize_reporting_data(data)
    file = open(filename, "w")
    if javascript_compatibility:
        file.write(JS_PREFIX)
    if pretty_formatting:
        file.write(json.dumps(report, indent=4, sort_keys=True))
    else:
        file.write(json.dumps(report))
    file.close()

def _unserialize_step_data(js):
    step = StepData(js["description"])
    for js_entry in js["entries"]:
        if js_entry["type"] == "log":
            entry = LogData(js_entry["level"], js_entry["message"])
        elif js_entry["type"] == "attachment":
            entry = AttachmentData(js_entry["description"], js_entry["filename"])
        elif js_entry["type"] == "check":
            entry = CheckData(js_entry["description"], js_entry["outcome"], js_entry["details"])
        step.entries.append(entry)
    return step

def _unserialize_test_data(js):
    test = TestData(js["id"], js["description"])
    test.outcome = js["outcome"]
    test.start_time = float(js["start_time"])
    test.end_time = float(js["end_time"])
    test.tags = js["tags"]
    test.properties = js["properties"]
    test.links = [ [link["url"], link["name"]] for link in js["links"] ]
    test.steps = [ _unserialize_step_data(s) for s in js["steps"] ]
    return test

def _unserialize_testsuite_data(js, parent=None):
    suite = TestSuiteData(js["id"], js["description"], parent)
    suite.tags = js["tags"]
    suite.properties = js["properties"]
    suite.links = [ [link["url"], link["name"]] for link in js["links"] ]

    if "before_suite" in js:
        suite.before_suite_start_time = float(js["before_suite"]["start_time"])
        suite.before_suite_end_time = float(js["before_suite"]["end_time"])
        suite.before_suite_steps = [ _unserialize_step_data(s) for s in js["before_suite"]["steps"] ]

    suite.tests = [ _unserialize_test_data(t) for t in js["tests"] ]
    
    if "after_suite" in js:
        suite.after_suite_start_time = float(js["after_suite"]["start_time"])
        suite.after_suite_end_time = float(js["after_suite"]["end_time"])
        suite.after_suite_steps = [ _unserialize_step_data(s) for s in js["after_suite"]["steps"] ]
    
    suite.sub_testsuites = [ _unserialize_testsuite_data(s, suite) for s in js["sub_suites"] ]
    
    return suite

def unserialize_reporting_data_from_file(filename):
    data = ReportingData()
    file = open(filename, "r")
    content = file.read()
    file.close()
    content = re.sub("^" + JS_PREFIX, "", content)
    js = json.loads(content)
    data.info = js["info"]
    data.stats = js["stats"]
    data.start_time = float(js["start_time"])
    data.end_time = float(js["end_time"])
    data.generation_time = float(js["generation_time"])
    data.testsuites = [ _unserialize_testsuite_data(s) for s in js["suites"] ]
    return data

class JsonBackend(ReportingBackend):
    name = "json"
    
    def __init__(self, javascript_compatibility=True, pretty_formatting=False):
        self.javascript_compatibility = javascript_compatibility
        self.pretty_formatting = pretty_formatting
    
    def end_tests(self):
        serialize_reporting_data_into_file(
            self.reporting_data, self.report_dir + "/report.json",
            javascript_compatibility=self.javascript_compatibility, pretty_formatting=self.pretty_formatting
        )
