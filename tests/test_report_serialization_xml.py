'''
Created on Nov 17, 2016

@author: nicolas
'''

import six
import pytest

from lemoncheesecake.reporting.backends.xml import XmlBackend, load_report_from_file, save_report_into_file
from lemoncheesecake.exceptions import InvalidReportFile, IncompatibleReportFile

try:
    import lxml
    from lxml import etree as ET
except ImportError:
    pass
else:
    from helpers.reporttests import *  # import the actual tests against XML serialization

    @pytest.fixture(scope="function")
    def backend():
        return XmlBackend()

    @pytest.fixture()
    def serialization_tester():
        return do_test_serialization

    def test_load_report_non_xml(tmpdir):
        file = tmpdir.join("report.xml")
        file.write("foobar")
        with pytest.raises(InvalidReportFile):
            load_report_from_file(file.strpath)

    def test_load_report_bad_xml(tmpdir):
        file = tmpdir.join("report.xml")
        file.write("<value>foobar</value>")
        with pytest.raises(InvalidReportFile):
            load_report_from_file(file.strpath)

    def test_load_report_incompatible_version(report_in_progress, tmpdir):
        filename = tmpdir.join("report.xml").strpath
        save_report_into_file(report_in_progress, filename)
        with open(filename, "r") as fh:
            xml = ET.parse(fh)
        root = xml.getroot().xpath("/lemoncheesecake-report")[0]
        root.attrib["report-version"] = "2.0"
        if six.PY3:
            xml_content = ET.tostring(root, pretty_print=True, encoding="unicode")
        else:
            xml_content = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")

        with open(filename, "w") as fh:
            fh.write(xml_content)

        with pytest.raises(IncompatibleReportFile):
            load_report_from_file(filename)
