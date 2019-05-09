'''
Created on Dec 10, 2016

@author: nicolas
'''

import os
import os.path as osp
import sys
import shutil
import argparse

from typing import List, Any

from lemoncheesecake.suite import load_suites_from_directory, Suite
from lemoncheesecake.fixtures import load_fixtures_from_directory, Fixture
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.reporting import ConsoleBackend, HtmlBackend, JsonBackend, XmlBackend, JunitBackend, \
    ReportPortalBackend, SlackReportingBackend, filter_available_reporting_backends
from lemoncheesecake.reporting.backend import ReportingBackend
from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation
from lemoncheesecake.exceptions import ProjectError, UserError, serialize_current_exception
from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.helpers.moduleimport import import_module

PROJECT_CONFIG_FILE = "project.py"


class Project(object):
    def __init__(self, project_dir):
        self.dir = project_dir
        self.report_title = None
        self.is_threaded = True
        self.hide_command_line_in_report = False
        self.console_backend = ConsoleBackend()
        self.json_backend = JsonBackend()
        self.xml_backend = XmlBackend()
        self.junit_backend = JunitBackend()
        self.html_backend = HtmlBackend()
        self.reportportal_backend = ReportPortalBackend()
        self.slack_backend = SlackReportingBackend()

    def add_custom_cli_args(self, cli_parser):
        # type: (argparse.ArgumentParser) -> None
        pass

    def create_report_dir(self):
        # type: () -> str
        return create_report_dir_with_rotation(self.dir)

    def get_suites(self):
        # type: () -> List[Suite]
        return load_suites_from_directory(osp.join(self.dir, "suites"))

    def get_metadata_policy(self):
        # type: () -> MetadataPolicy
        return MetadataPolicy()

    def get_suites_strict(self):
        # type: () -> List[Suite]
        suites = self.get_suites()
        policy = self.get_metadata_policy()
        policy.check_suites_compliance(suites)
        return suites

    def get_fixtures(self):
        # type: () -> List[Fixture]
        fixtures_dir = osp.join(self.dir, "fixtures")
        if osp.exists(fixtures_dir):
            return load_fixtures_from_directory(fixtures_dir)
        else:
            return []

    def get_all_reporting_backends(self):
        # type: () -> List[ReportingBackend]
        return filter_available_reporting_backends((
            self.console_backend, self.json_backend, self.html_backend,
            self.xml_backend, self.junit_backend, self.reportportal_backend,
            self.slack_backend
        ))

    def get_default_reporting_backends_for_test_run(self):
        # type: () -> List[ReportingBackend]
        return filter_available_reporting_backends((
            self.console_backend, self.json_backend, self.html_backend
        ))

    def pre_run(self, cli_args, report_dir):
        # type: (Any, str) -> None
        pass

    def post_run(self, cli_args, report_dir):
        # type: (Any, str) -> None
        pass

    def get_report_info(self):
        # type: () -> List
        info = []
        if not self.hide_command_line_in_report:
            info.append(("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:])))
        return info

    def on_test_session_start(self, event):
        title = self.report_title
        if title is not None:
            event.report.title = self.report_title

        for key, value in self.get_report_info():
            event.report.add_info(key, value)


def _find_file_in_parent_directories(filename, dirname):
    if osp.exists(osp.join(dirname, filename)):
        return osp.join(dirname, filename)

    parent_dirname = osp.dirname(dirname)
    if parent_dirname == dirname:
        return None  # root directory has been reached

    return _find_file_in_parent_directories(filename, parent_dirname)


def find_project_file():
    filename = os.environ.get("LCC_PROJECT_FILE")
    if filename is not None:
        return filename if osp.exists(filename) else None

    filename = _find_file_in_parent_directories(PROJECT_CONFIG_FILE, os.getcwd())
    return filename  # filename can be None


def find_project_dir():
    project_filename = find_project_file()
    if project_filename is None:
        return None
    return osp.dirname(project_filename)


def create_project(project_dir):
    shutil.copyfile(get_resource_path(("project", "template.py")), osp.join(project_dir, PROJECT_CONFIG_FILE))
    os.mkdir(osp.join(project_dir, "suites"))
    os.mkdir(osp.join(project_dir, "fixtures"))


def load_project_from_file(project_filename):
    project_dir = osp.dirname(project_filename)

    # load project module
    try:
        project_module = import_module(project_filename)
    except UserError as e:
        raise e  # propagate UserError
    except Exception:
        raise ProjectError("Got an unexpected error while loading project:%s" % (
            serialize_current_exception()
        ))
    
    # get project config instance
    try:
        project = project_module.project
    except AttributeError:
        raise ProjectError("Cannot find symbol 'project' in module '%s'" % project_filename)
    if not isinstance(project, Project):
        raise ProjectError("Symbol 'project' in module '%s' does not inherit lemoncheesecake.project.Project" % project_filename)
    
    return project


def load_project_from_dir(project_dir):
    return load_project_from_file(osp.join(project_dir, PROJECT_CONFIG_FILE))


def load_project():
    project_filename = find_project_file()
    if project_filename is None:
        raise ProjectError("Cannot find project file")

    return load_project_from_file(project_filename)
