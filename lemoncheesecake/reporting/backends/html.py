import os
import os.path as osp
from shutil import copy

from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSessionBuilderMixin, ReportingSession
from lemoncheesecake.helpers.console import bold


class HtmlReportWriter(ReportingSession):
    def __init__(self, report_dir):
        self.report_dir = report_dir

    def on_test_session_start(self, _):
        src_dir = get_resource_path("html")
        resources_dir = osp.join(self.report_dir, ".html")

        os.mkdir(resources_dir)
        copy(osp.join(src_dir, "report.js"), resources_dir)
        copy(osp.join(src_dir, "report.css"), resources_dir)
        copy(osp.join(src_dir, "logo.png"), resources_dir)
        copy(osp.join(src_dir, "report.html"), self.report_dir)

    def on_test_session_end(self, _):
        print("%s : file://%s/report.html" % (bold("HTML report"), self.report_dir))
        print()


class HtmlBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def get_name(self):
        return "html"

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        return HtmlReportWriter(report_dir)
