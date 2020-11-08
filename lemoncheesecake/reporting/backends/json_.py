'''
Created on Mar 27, 2016

@author: nicolas
'''

import re
import json
from collections import OrderedDict
import time

import lemoncheesecake
from lemoncheesecake.reporting.backend import FileReportBackend, ReportUnserializerMixin
from lemoncheesecake.reporting.report import (
    Report, Log, Check, Attachment, Url, Step, Result, TestResult, SuiteResult,
    format_time_as_iso8601, parse_iso8601_time
)
from lemoncheesecake.exceptions import ReportLoadingError

JS_PREFIX = "var reporting_data = "


def _serialize_time(t):
    return format_time_as_iso8601(t) if t is not None else None


def _odict(*args):
    d = OrderedDict()
    i = 0
    while i < len(args):
        d[args[i]] = args[i+1]
        i += 2
    return d


def _serialize_steps(steps):
    json_steps = []
    for step in steps:
        json_step = _odict(
            "description", step.description,
            "start_time", _serialize_time(step.start_time),
            "end_time", _serialize_time(step.end_time),
            "entries", []
        )
        json_steps.append(json_step)
        for log in step.get_logs():
            if isinstance(log, Log):
                json_log = _odict(
                    "type", "log",
                    "level", log.level,
                    "message", log.message,
                    "time", _serialize_time(log.time)
                )
            elif isinstance(log, Attachment):
                json_log = _odict(
                    "type", "attachment",
                    "description", log.description,
                    "filename", log.filename,
                    "as_image", log.as_image,
                    "time", _serialize_time(log.time)
                )
            elif isinstance(log, Url):
                json_log = _odict(
                    "type", "url",
                    "description", log.description,
                    "url", log.url,
                    "time", _serialize_time(log.time)
                )
            elif isinstance(log, Check):
                json_log = _odict(
                    "type", "check",
                    "description", log.description,
                    "is_successful", log.is_successful,
                    "details", log.details,
                    "time", _serialize_time(log.time)
                )
            else:
                raise ValueError("Don't know how to handle step log %s" % log)
            json_step["entries"].append(json_log)
    return json_steps


def _serialize_node_metadata(node, json_node):
    json_node.update(_odict(
        "name", node.name, "description", node.description,
        "tags", node.tags,
        "properties", node.properties,
        "links", [_odict("name", link[1], "url", link[0]) for link in node.links]
    ))


def _serialize_result(result):
    return _odict(
        "start_time", _serialize_time(result.start_time),
        "end_time", _serialize_time(result.end_time),
        "steps", _serialize_steps(result.get_steps()),
        "status", result.status,
        "status_details", result.status_details
    )


def _serialize_test_result(test):
    json_test = _serialize_result(test)
    _serialize_node_metadata(test, json_test)
    return json_test


def _serialize_suite_result(suite):
    json_suite = _odict(
        "start_time", _serialize_time(suite.start_time),
        "end_time", _serialize_time(suite.end_time),
        "tests", list(map(_serialize_test_result, suite.get_tests())),
        "suites", list(map(_serialize_suite_result, suite.get_suites()))
    )
    _serialize_node_metadata(suite, json_suite)
    if suite.suite_setup:
        json_suite["suite_setup"] = _serialize_result(suite.suite_setup)
    if suite.suite_teardown:
        json_suite["suite_teardown"] = _serialize_result(suite.suite_teardown)

    return json_suite


def serialize_report_into_json(report):
    json_report = _odict(
        "lemoncheesecake_version", lemoncheesecake.__version__,
        "report_version", 1.1,
        "start_time", _serialize_time(report.start_time),
        "end_time", _serialize_time(report.end_time),
        "generation_time", _serialize_time(time.time()),
        "nb_threads", report.nb_threads,
        "title", report.title,
        "info", [[n, v] for n, v in report.info]
    )

    if report.test_session_setup:
        json_report["test_session_setup"] = _serialize_result(report.test_session_setup)

    json_report["suites"] = list(map(_serialize_suite_result, report.get_suites()))

    if report.test_session_teardown:
        json_report["test_session_teardown"] = _serialize_result(report.test_session_teardown)

    return json_report


def save_report_into_file(report, filename, javascript_compatibility=True, pretty_formatting=False):
    json_report = serialize_report_into_json(report)
    with open(filename, "w") as fh:
        if javascript_compatibility:
            fh.write(JS_PREFIX)
        if pretty_formatting:
            fh.write(json.dumps(json_report, indent=4))
        else:
            fh.write(json.dumps(json_report))


def _unserialize_time(t):
    return parse_iso8601_time(t) if t is not None else None


def _unserialize_step(json_step):
    step = Step(json_step["description"])
    step.start_time = _unserialize_time(json_step["start_time"])
    step.end_time = _unserialize_time(json_step["end_time"])
    for json_log in json_step["entries"]:
        if json_log["type"] == "log":
            step_log = Log(
                json_log["level"], json_log["message"], _unserialize_time(json_log["time"])
            )
        elif json_log["type"] == "attachment":
            step_log = Attachment(
                json_log["description"], json_log["filename"], json_log["as_image"],
                _unserialize_time(json_log["time"])
            )
        elif json_log["type"] == "url":
            step_log = Url(
                json_log["description"], json_log["url"], _unserialize_time(json_log["time"])
            )
        elif json_log["type"] == "check":
            step_log = Check(
                json_log["description"], json_log["is_successful"], json_log["details"],
                _unserialize_time(json_log["time"])
            )
        else:
            raise ValueError("Unknown step log type '%s'" % json_log["type"])
        step.add_log(step_log)
    return step


def _unserialize_result(json_result, result):
    result.status = json_result["status"]
    # status_details for non-test results has been introduced in report version 1.1:
    result.status_details = json_result.get("status_details", None)
    result.start_time = _unserialize_time(json_result["start_time"])
    result.end_time = _unserialize_time(json_result["end_time"])
    for json_step in json_result["steps"]:
        result.add_step(_unserialize_step(json_step))

    return result


def _unserialize_node_metadata(json_node, node):
    node.tags = json_node["tags"]
    node.properties = json_node["properties"]
    node.links = [(link["url"], link["name"]) for link in json_node["links"]]


def _unserialize_test_result(json_test):
    test = TestResult(json_test["name"], json_test["description"])
    _unserialize_result(json_test, test)
    _unserialize_node_metadata(json_test, test)
    return test


def _unserialize_suite_result(json_suite):
    suite = SuiteResult(json_suite["name"], json_suite["description"])
    _unserialize_node_metadata(json_suite, suite)
    suite.start_time = _unserialize_time(json_suite["start_time"])
    suite.end_time = _unserialize_time(json_suite["end_time"])

    if "suite_setup" in json_suite:
        suite.suite_setup = Result()
        _unserialize_result(json_suite["suite_setup"], suite.suite_setup)

    for json_test in json_suite["tests"]:
        suite.add_test(_unserialize_test_result(json_test))

    if "suite_teardown" in json_suite:
        suite.suite_teardown = Result()
        _unserialize_result(json_suite["suite_teardown"], suite.suite_teardown)

    for json_sub_suite in json_suite["suites"]:
        suite.add_suite(_unserialize_suite_result(json_sub_suite))

    return suite


def _unserialize_report(json_report):
    report = Report()

    report.title = json_report["title"]
    report.info = json_report["info"]
    report.start_time = _unserialize_time(json_report["start_time"])
    report.end_time = _unserialize_time(json_report["end_time"])
    report.saving_time = _unserialize_time(json_report["generation_time"])
    report.nb_threads = json_report["nb_threads"]

    if "test_session_setup" in json_report:
        report.test_session_setup = Result()
        _unserialize_result(json_report["test_session_setup"], report.test_session_setup)

    for json_suite in json_report["suites"]:
        report.add_suite(_unserialize_suite_result(json_suite))

    if "test_session_teardown" in json_report:
        report.test_session_teardown = Result()
        _unserialize_result(json_report["test_session_teardown"], report.test_session_teardown)

    return report


def load_report_from_file(filename):
    try:
        with open(filename, "r") as fh:
            js_content = fh.read()
    except IOError as e:
        raise e  # re-raise as-is

    js_content = re.sub("^" + JS_PREFIX, "", js_content)

    try:
        js = json.loads(js_content)
    except ValueError as e:
        raise ReportLoadingError(str(e))

    report_version = js.get("report_version")
    if report_version is None:
        raise ReportLoadingError("Cannot find 'report_version' in JSON")
    if report_version >= 2.0:
        raise ReportLoadingError("Incompatible report version: got %s while 1.x is supported" % report_version)

    return _unserialize_report(js)


class JsonBackend(FileReportBackend, ReportUnserializerMixin):
    def __init__(self, javascript_compatibility=True, pretty_formatting=False):
        self.javascript_compatibility = javascript_compatibility
        self.pretty_formatting = pretty_formatting

    def get_name(self):
        return "json"

    def get_report_filename(self):
        return "report.js"

    def save_report(self, filename, report):
        save_report_into_file(
            report, filename,
            javascript_compatibility=self.javascript_compatibility, pretty_formatting=self.pretty_formatting
        )

    def load_report(self, path):
        report = load_report_from_file(path)
        report.bind(self, path)
        return report
