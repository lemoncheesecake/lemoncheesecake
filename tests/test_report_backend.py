import time

import pytest

from lemoncheesecake.reporting import Report, load_report
from lemoncheesecake.reporting.backends.xml import serialize_report_into_file as xml_save
from lemoncheesecake.reporting.backends.json_ import serialize_report_into_file as json_save

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
    xml_save(sample_report, tmpdir.join("report.xml").strpath, indent_level=4)
    report, backend = load_report(tmpdir.join("report.xml").strpath)
    assert backend.name == "xml"
    assert_report(report, sample_report)

def test_load_report_json(tmpdir, sample_report):
    json_save(sample_report, tmpdir.join("report.json").strpath)
    report, backend = load_report(tmpdir.join("report.json").strpath)
    assert backend.name == "json"
    assert_report(report, sample_report)