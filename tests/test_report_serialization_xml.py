import sys
import xml.etree.ElementTree as ET

import pytest

from lemoncheesecake.reporting.backends.xml import XmlBackend, load_report_from_file, save_report_into_file
from lemoncheesecake.exceptions import ReportLoadingError

from helpers.reporttests import ReportSerializationTests, report_in_progress


class TestXmlSerialization(ReportSerializationTests):
    backend = XmlBackend()
    # it inherits all the actual serialization tests

    @pytest.mark.skipif(sys.platform.startswith("win") and sys.version_info < (3, 9),
                        reason="This test fails specifically on Github Actions with Python 3.8 running on Windows")
    def test_unicode(self):
        super().test_unicode()


def test_load_report_non_xml(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("foobar")
    with pytest.raises(ReportLoadingError):
        load_report_from_file(file.strpath)


def test_load_report_bad_xml(tmpdir):
    file = tmpdir.join("report.xml")
    file.write("<value>foobar</value>")
    with pytest.raises(ReportLoadingError):
        load_report_from_file(file.strpath)


def test_load_report_incompatible_version(report_in_progress, tmpdir):
    filename = tmpdir.join("report.xml").strpath
    save_report_into_file(report_in_progress, filename)
    with open(filename, "r") as fh:
        xml = ET.parse(fh)
    root = xml.getroot()
    root.attrib["report-version"] = "2.0"
    xml_content = ET.tostring(root, encoding="unicode", xml_declaration=True)

    with open(filename, "w") as fh:
        fh.write(xml_content)

    with pytest.raises(ReportLoadingError, match="Incompatible"):
        load_report_from_file(filename)
