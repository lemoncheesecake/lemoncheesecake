'''
Created on Nov 17, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake.reporting.backends.xml import XmlBackend, unserialize_report_from_file
from lemoncheesecake.exceptions import InvalidReportFile

try:
    import lxml
except ImportError:
    pass
else:
    from report_serialization_tests import *

@pytest.fixture
def backend():
    return XmlBackend()

def test_unserialize_non_xml(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("foobar")
    with pytest.raises(InvalidReportFile):
        unserialize_report_from_file(file.strpath)

def test_unserialize_bad_xml(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("<value>foobar</value>")
    with pytest.raises(InvalidReportFile):
        unserialize_report_from_file(file.strpath)