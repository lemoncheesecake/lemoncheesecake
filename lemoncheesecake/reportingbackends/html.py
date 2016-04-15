'''
Created on Mar 19, 2016

@author: nicolas
'''

import sys
import re
import os
import os.path as p
from shutil import copy, copytree

from lemoncheesecake.reporting import ReportingBackend

OFFLINE_MODE = False

class HtmlBackend(ReportingBackend):
    def begin_tests(self):
        html_resource_dir = p.join(p.dirname(__file__), p.pardir, "resources", "html")
        report_resource_dir = p.join(self.report_dir, ".html") 
        
        os.mkdir(report_resource_dir)
        copy(p.join(html_resource_dir, "report.js"), report_resource_dir)
        
        if OFFLINE_MODE:
            copy(p.join(html_resource_dir, "report_offline.html"), p.join(self.report_dir, "report.html"))
            copy(p.join(html_resource_dir, "jquery-1.12.3.min.js"), report_resource_dir)
            copytree(p.join(html_resource_dir, "bootstrap-3.3.6-dist"), p.join(report_resource_dir, "bootstrap-3.3.6-dist"))
        else:
            copy(p.join(html_resource_dir, "report.html"), self.report_dir)
