'''
Created on Nov 19, 2016

@author: nicolas
'''

import json

import pytest

from lemoncheesecake.reporting.backends.json_ import JsonBackend, load_report_from_file, save_report_into_file
from lemoncheesecake.exceptions import InvalidReportFile, IncompatibleReportFile

from helpers.reporttests import *  # import the actual tests against JSON serialization


@pytest.fixture(scope="function")
def backend():
    return JsonBackend()


@pytest.fixture()
def serialization_tester():
    return do_test_serialization


def test_load_report_non_json(tmpdir):
    file = tmpdir.join("report.js")
    file.write("foobar")
    with pytest.raises(InvalidReportFile):
        load_report_from_file(file.strpath)


def test_load_report_bad_json(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("{'foo': 'bar'}")
    with pytest.raises(InvalidReportFile):
        load_report_from_file(file.strpath)


def test_load_report_incompatible_version(report_in_progress, tmpdir):
    filename = tmpdir.join("report.json").strpath
    save_report_into_file(report_in_progress, filename, javascript_compatibility=False)
    with open(filename) as fh:
        report_data = json.load(fh)
    report_data["report_version"] = 2.0
    with open(filename, "w") as fh:
        json.dump(report_data, fh)

    with pytest.raises(IncompatibleReportFile):
        load_report_from_file(filename)
