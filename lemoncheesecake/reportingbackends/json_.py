'''
Created on Mar 27, 2016

@author: nicolas
'''

from lemoncheesecake.reportingdata import *
from lemoncheesecake.reporting import ReportingBackend

import json

def _time_value(value):
    return "%.3f" % value if value else None

def _serialize_steps_with_log_only(steps):
    json_steps = [ ]
    for step in steps:
        json_step = { "description": step.description, "logs": [ ] }
        json_steps.append(json_step)
        for entry in step.entries:
            json_step["logs"].append({ "level": entry.level, "message": entry.message })
    return json_steps

def _serialize_test_data(test):
    json_test = { 
        "id": test.id, "description": test.description,
        "start_time": _time_value(test.start_time),
        "end_time": _time_value(test.end_time),
        "tags": test.tags,
        "tickets": [ { "id": t[0], "url": t[1] } for t in test.tickets ],
        "steps": [ ],
        "outcome": test.outcome
    }
        
    for step in test.steps:
        json_step = { "description": step.description, "entries": [ ] }
        json_test["steps"].append(json_step)
        for entry in step.entries:
            if isinstance(entry, LogData):
                json_step["entries"].append({ "type": "log", "level": entry.level, "message": entry.message })
            else: # TestCheck
                json_step["entries"].append({ "type": "check", "description": entry.description, "outcome": entry.outcome })
    return json_test

def _serialize_testsuite_data(suite):
    return {
        "id": suite.id, "description": suite.description, "tags": suite.tags,
        "tickets": [ { "id": t[0], "url": t[1] } for t in suite.tickets ],
        "before_suite": {
            "start_time": _time_value(suite.before_suite_start_time),
            "end_time": _time_value(suite.before_suite_end_time),
            "steps": _serialize_steps_with_log_only(suite.before_suite_steps)
        },
        "after_suite": {
            "start_time": _time_value(suite.after_suite_start_time),
            "end_time": _time_value(suite.after_suite_end_time),
            "steps": _serialize_steps_with_log_only(suite.after_suite_steps)
        },
        "tests": [ _serialize_test_data(t) for t in suite.tests ],
        "sub_suites": [ _serialize_testsuite_data(s) for s in suite.sub_testsuites ]
    }

def serialize_reporting_data(data):
    return {
        "start_time": _time_value(data.start_time),
        "end_time": _time_value(data.end_time),
        "generation_time": _time_value(data.report_generation_time),
        "suites": [ _serialize_testsuite_data(s) for s in data.testsuites ],
        "info": [ [ n, v ] for n, v in data.info ],
        "stats": [ [ n, v ] for n, v in data.stats ]
    }

def serialize_reporting_data_into_file(data, filename, javascript_compatibility=True):
    report = serialize_reporting_data(data)
    file = open(filename, "w")
    if javascript_compatibility:
        file.write("var reporting_data = ")
    file.write(json.dumps(report))
    file.close()

class JsonBackend(ReportingBackend):
    def __init__(self, javascript_compatibility=True):
        self.javascript_compatibility=True
    
    def end_tests(self):
        serialize_reporting_data_into_file(self.reporting_data, self.report_dir + "/report.json", javascript_compatibility=True)