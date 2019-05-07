'''
Created on Mar 19, 2016

@author: nicolas
'''

import os
import os.path as p
from shutil import copy, copytree

from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession, ReportingSessionBuilderMixin


class HtmlReportWriter(ReportingSession):
    def __init__(self, report_dir, offline_mode):
        self.report_dir = report_dir
        self.offline_mode = offline_mode

    def on_test_session_start(self, event):
        html_resource_dir = get_resource_path("html")
        report_resource_dir = p.join(self.report_dir, ".html")

        os.mkdir(report_resource_dir)
        copy(p.join(html_resource_dir, "report.js"), report_resource_dir)
        copy(p.join(html_resource_dir, "report.css"), report_resource_dir)

        if self.offline_mode:
            copy(p.join(html_resource_dir, "report_offline.html"), p.join(self.report_dir, "report.html"))
            copy(p.join(html_resource_dir, "jquery-1.12.3.min.js"), report_resource_dir)
            copytree(p.join(html_resource_dir, "bootstrap-3.3.6-dist"),
                     p.join(report_resource_dir, "bootstrap-3.3.6-dist"))
            copy(p.join(html_resource_dir, "bootstrap-slate.min.css"),
                 p.join(report_resource_dir, "bootstrap-3.3.6-dist", "css", "bootstrap.min.css"))
        else:
            copy(p.join(html_resource_dir, "report.html"), self.report_dir)


class HtmlBackend(ReportingBackend, ReportingSessionBuilderMixin):
    name = "html"

    def __init__(self, offline_mode=False):
        self.offline_mode = offline_mode

    def create_reporting_session(self, report_dir, report, parallel, saving_strategy):
        return HtmlReportWriter(report_dir, self.offline_mode)
