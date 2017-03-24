import time

import pytest

from lemoncheesecake.reporting import Report, load_report, save_report, XmlBackend, JsonBackend
from lemoncheesecake.reporting.backends.xml import \
    save_report_into_file as xml_save, \
    load_report_from_file as xml_load
from lemoncheesecake.reporting.backends.json_ import \
    save_report_into_file as json_save, \
    load_report_from_file as json_load

from helpers import assert_report

@pytest.fixture()
def sample_report():
    report = Report()
    ts = time.time()
    report.start_time = ts
    report.end_time = ts
    report.report_generation_time = ts
    return report

def test_load_report_xml(tmpdir, sample_report):
    filename = tmpdir.join("report.xml").strpath
    xml_save(sample_report, filename, indent_level=4)
    report, backend = load_report(tmpdir.join("report.xml").strpath)
    assert backend.name == "xml"
    assert_report(report, sample_report)

def test_load_report_json(tmpdir, sample_report):
    filename = tmpdir.join("report.json").strpath
    json_save(sample_report, filename)
    report, backend = load_report(filename)
    assert backend.name == "json"
    assert_report(report, sample_report)

def test_save_report_xml(tmpdir, sample_report):
    filename = tmpdir.join("report.json").strpath
    save_report(filename, sample_report, XmlBackend())
    report = xml_load(filename)
    assert_report(report, sample_report)

def test_save_report_json(tmpdir, sample_report):
    filename = tmpdir.join("report.json").strpath
    save_report(filename, sample_report, JsonBackend())
    report = json_load(filename)
    assert_report(report, sample_report)