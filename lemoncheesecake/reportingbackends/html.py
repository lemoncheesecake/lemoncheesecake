'''
Created on Mar 19, 2016

@author: nicolas
'''

import sys
import re
import os
import os.path as p
from shutil import copy

from lemoncheesecake.reporting import ReportingBackend

class HtmlBackend(ReportingBackend):
    def begin_tests(self):
        html_resource_dir = p.join(p.dirname(__file__), p.pardir, "resources", "html")
        
        report_resource_dir = p.join(self.report_dir, ".html") 
        
        os.mkdir(report_resource_dir)
        copy(p.join(html_resource_dir, "report.html"), self.report_dir)
        copy(p.join(html_resource_dir, "report.js"), report_resource_dir)