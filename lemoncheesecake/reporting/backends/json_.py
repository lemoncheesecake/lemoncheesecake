'''
Created on Mar 27, 2016

@author: nicolas
'''

import re
import json
from collections import OrderedDict

import lemoncheesecake
from lemoncheesecake.reporting.backend import BoundReport, FileReportBackend
from lemoncheesecake.reporting.report import (
    Log, Check, Attachment, Url, Step, TestResult, SetupResult, SuiteResult,
    format_timestamp, parse_timestamp
)
from lemoncheesecake.exceptions import InvalidReportFile, ProgrammingError

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
            if isinstance(entry, Log):
                entry = _dict(
                    "type", "log",
                    "level", entry.level,
                    "message", entry.message,
                    "time", _serialize_time(entry.time)
                )
            elif isinstance(entry, Attachment):
                entry = _dict(
                    "type", "attachment",
                    "description", entry.description,
                    "filename", entry.filename,
                    "as_image", entry.as_image,
                    "time", _serialize_time(entry.time)
                )
            elif isinstance(entry, Url):
                entry = _dict(
                    "type", "url",
                    "description", entry.description,
                    "url", entry.url,
                    "time", _serialize_time(entry.time)
                )
            else:  # TestCheck
                entry = _dict(
                    "type", "check",
                    "description", entry.description,
                    "outcome", entry.outcome,
                    "details", entry.details,
                    "time", _serialize_time(entry.time)
                )
            json_step["entries"].append(entry)
    return json_steps


def _serialize_common_data(obj):
    return _dict(
        "name", obj.name, "description", obj.description,
        "tags", obj.tags,
        "properties", obj.properties,
        "links", [_dict("name", link[1], "url", link[0]) for link in obj.links]
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


def _serialize_suite_data(suite):
    json_suite = _serialize_common_data(suite)
    json_suite.update(_dict(
        "start_time", _serialize_time(suite.start_time),
        "end_time", _serialize_time(suite.end_time),
        "tests", [_serialize_test_data(t) for t in suite.get_tests()],
        "suites", [_serialize_suite_data(s) for s in suite.get_suites()]
    ))
    if suite.suite_setup:
        json_suite["suite_setup"] = _serialize_hook_data(suite.suite_setup)
    if suite.suite_teardown:
        json_suite["suite_teardown"] = _serialize_hook_data(suite.suite_teardown)

    return json_suite


def serialize_report_into_json(report):
    serialized = _dict(
        "lemoncheesecake_version", lemoncheesecake.__version__,
        "lemoncheesecake_report_version", 1.0,
        "start_time", _serialize_time(report.start_time),
        "end_time", _serialize_time(report.end_time),
        "generation_time", _serialize_time(report.report_generation_time),
        "nb_threads", report.nb_threads,
        "title", report.title,
        "info", [[n, v] for n, v in report.info],
        "stats", [[n, v] for n, v in report.serialize_stats()]
    )

    if report.test_session_setup:
        serialized["test_session_setup"] = _serialize_hook_data(report.test_session_setup)

    serialized["suites"] = [_serialize_suite_data(s) for s in report.get_suites()]

    if report.test_session_teardown:
        serialized["test_session_teardown"] = _serialize_hook_data(report.test_session_teardown)

    return serialized


def save_report_into_file(data, filename, javascript_compatibility=True, pretty_formatting=False):
    report = serialize_report_into_json(data)
    with open(filename, "w") as fh:
        if javascript_compatibility:
            fh.write(JS_PREFIX)
        if pretty_formatting:
            fh.write(json.dumps(report, indent=4))
        else:
            fh.write(json.dumps(report))


def _unserialize_step_data(js):
    step = Step(js["description"])
    step.start_time = parse_timestamp(js["start_time"])
    step.end_time = parse_timestamp(js["end_time"]) if js["end_time"] else None
    for js_entry in js["entries"]:
        if js_entry["type"] == "log":
            entry = Log(
                js_entry["level"], js_entry["message"], parse_timestamp(js_entry["time"])
            )
        elif js_entry["type"] == "attachment":
            entry = Attachment(
                js_entry["description"], js_entry["filename"], js_entry["as_image"], parse_timestamp(js_entry["time"])
            )
        elif js_entry["type"] == "url":
            entry = Url(
                js_entry["description"], js_entry["url"], parse_timestamp(js_entry["time"])
            )
        elif js_entry["type"] == "check":
            entry = Check(
                js_entry["description"], js_entry["outcome"], js_entry["details"], parse_timestamp(js_entry["time"])
            )
        else:
            raise ProgrammingError("Unknown entry type '%s'" % js_entry["type"])
        step.entries.append(entry)
    return step


def _unserialize_test_data(js):
    test = TestResult(js["name"], js["description"])
    test.status = js["status"]
    test.status_details = js["status_details"]
    test.start_time = parse_timestamp(js["start_time"])
    test.end_time = parse_timestamp(js["end_time"]) if js["end_time"] else None
    test.tags = js["tags"]
    test.properties = js["properties"]
    test.links = [(link["url"], link["name"]) for link in js["links"]]
    test.steps = [_unserialize_step_data(s) for s in js["steps"]]
    return test


def _unserialize_hook_data(js):
    data = SetupResult()
    data.outcome = js["outcome"]
    data.start_time = parse_timestamp(js["start_time"])
    data.end_time = parse_timestamp(js["end_time"]) if js["end_time"] else None
    data.steps = [_unserialize_step_data(s) for s in js["steps"]]

    return data


def _unserialize_suite_data(js):
    suite = SuiteResult(js["name"], js["description"])
    suite.start_time = parse_timestamp(js["start_time"])
    suite.end_time = parse_timestamp(js["end_time"]) if js["end_time"] else None
    suite.tags = js["tags"]
    suite.properties = js["properties"]
    suite.links = [(link["url"], link["name"]) for link in js["links"]]

    if "suite_setup" in js:
        suite.suite_setup = _unserialize_hook_data(js["suite_setup"])

    for js_test in js["tests"]:
        test = _unserialize_test_data(js_test)
        suite.add_test(test)

    if "suite_teardown" in js:
        suite.suite_teardown = _unserialize_hook_data(js["suite_teardown"])

    for js_suite in js["suites"]:
        sub_suite = _unserialize_suite_data(js_suite)
        suite.add_suite(sub_suite)

    return suite


def load_report_from_file(filename):
    report = BoundReport()
    try:
        with open(filename, "r") as fh:
            js_content = fh.read()
    except IOError as e:
        raise e  # re-raise as-is

    js_content = re.sub("^" + JS_PREFIX, "", js_content)

    try:
        js = json.loads(js_content)
    except ValueError as e:
        raise InvalidReportFile(str(e))

    if "lemoncheesecake_report_version" not in js:
        raise InvalidReportFile("Cannot find 'lemoncheesecake_report_version' in JSON")

    report.title = js["title"]
    report.info = js["info"]
    report.start_time = parse_timestamp(js["start_time"])
    report.end_time = parse_timestamp(js["end_time"]) if js["end_time"] else None
    report.report_generation_time = parse_timestamp(js["generation_time"]) if js["generation_time"] else None
    report.nb_threads = js["nb_threads"]

    if "test_session_setup" in js:
        report.test_session_setup = _unserialize_hook_data(js["test_session_setup"])

    for js_suite in js["suites"]:
        suite = _unserialize_suite_data(js_suite)
        report.add_suite(suite)

    if "test_session_teardown" in js:
        report.test_session_teardown = _unserialize_hook_data(js["test_session_teardown"])

    return report


class JsonBackend(FileReportBackend):
    name = "json"

    def __init__(self, javascript_compatibility=True, pretty_formatting=False):
        self.javascript_compatibility = javascript_compatibility
        self.pretty_formatting = pretty_formatting

    def get_report_filename(self):
        return "report.js"

    def save_report(self, filename, report):
        save_report_into_file(
            report, filename,
            javascript_compatibility=self.javascript_compatibility, pretty_formatting=self.pretty_formatting
        )

    def load_report(self, filename):
        return load_report_from_file(filename).bind(self, filename)
