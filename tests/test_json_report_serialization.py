'''
Created on Nov 19, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake.reporting.backends.json_ import JsonBackend, load_report_from_file
from lemoncheesecake.exceptions import InvalidReportFile

from report_serialization_tests import *

@pytest.fixture
def backend():
    return JsonBackend()

def test_load_report_non_json(tmpdir):
    file = tmpdir.join("report.json")
    file.write("foobar")
    with pytest.raises(InvalidReportFile):
        load_report_from_file(file.strpath)

def test_load_report_bad_json(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("{'foo': 'bar'}")
    with pytest.raises(InvalidReportFile):
        load_report_from_file(file.strpath)