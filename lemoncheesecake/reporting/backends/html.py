import os
import os.path as osp
from shutil import copy, copytree

from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSessionBuilderMixin, ReportingSession
from lemoncheesecake.helpers.console import bold


class HtmlReportWriter(ReportingSession):
    def __init__(self, report_dir, fat_html):
        self.report_dir = report_dir
        self.fat_html = fat_html

    def on_test_session_start(self, _):
        src_dir = get_resource_path("html")
        dst_dir = osp.join(self.report_dir, ".html")

        os.mkdir(dst_dir)
        copy(osp.join(src_dir, "report.js"), dst_dir)
        copy(osp.join(src_dir, "report.css"), dst_dir)
        copy(osp.join(src_dir, "logo.png"), dst_dir)

        if self.fat_html:
            copy(osp.join(src_dir, "report_static.html"), osp.join(self.report_dir, "report.html"))
            copy(osp.join(src_dir, "jquery-1.12.3.min.js"), dst_dir)
            copytree(osp.join(src_dir, "bootstrap-3.3.6-dist"), osp.join(dst_dir, "bootstrap-3.3.6-dist"))
            copy(osp.join(src_dir, "bootstrap-slate.min.css"), osp.join(dst_dir, "bootstrap-3.3.6-dist", "css", "bootstrap.min.css"))
        else:
            copy(osp.join(src_dir, "report_external.html"), osp.join(self.report_dir, "report.html"))

    def on_test_session_end(self, _):
        print("%s : file://%s/report.html" % (bold("HTML report"), self.report_dir))
        print()


class HtmlBackend(ReportingBackend, ReportingSessionBuilderMixin):
    def __init__(self):
        self.fat_html = True

    def get_name(self):
        return "html"

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        return HtmlReportWriter(report_dir, self.fat_html)
