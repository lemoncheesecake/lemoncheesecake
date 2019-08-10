'''
Created on Dec 10, 2016

@author: nicolas
'''

import sys
import os
import os.path as osp
import shutil
import argparse

from typing import Any, Dict, Optional, Sequence, Tuple, List

from lemoncheesecake.suite import load_suites_from_directory, Suite
from lemoncheesecake.fixture import load_fixtures_from_directory, Fixture
from lemoncheesecake.metadatapolicy import MetadataPolicy
from lemoncheesecake.reporting import get_reporting_backends, ReportingBackend
from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation
from lemoncheesecake.exceptions import ProjectError, UserError, serialize_current_exception
from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.helpers.moduleimport import import_module

PROJECT_CONFIG_FILE = "project.py"
DEFAULT_REPORTING_BACKENDS = ("console", "json", "html")


class Project(object):
    def __init__(self, project_dir):
        #: The project's directory path
        self.dir = project_dir  # type: str
        #: The project's metadata policy
        self.metadata_policy = MetadataPolicy()
        #: Indicates whether or not the project supports parallel execution of tests
        self.threaded = True  # type: bool
        #: Indicated whether or not the command line ("lcc run...") will be displayed in the report
        self.show_command_line_in_report = True  # type: bool
        #: The reporting backends of the project as a dict (whose key is the reporting backend name)
        self.reporting_backends = {b.get_name(): b for b in get_reporting_backends()}  # type: Dict[str, ReportingBackend]
        #: The list of default reporting backend (indicated by their name) that will be used by "lcc run"
        self.default_reporting_backend_names = list(DEFAULT_REPORTING_BACKENDS)

    def add_cli_args(self, cli_parser):
        # type: (argparse.ArgumentParser) -> None
        """
        Overridable. This method can be used to add extra CLI arguments to "lcc run".
        """
        pass

    def create_report_dir(self):
        # type: () -> str
        """
        Overridable. Create the report directory when no report directory is specified to "lcc run".
        """
        return create_report_dir_with_rotation(self.dir)

    def load_suites(self):
        # type: () -> Sequence[Suite]
        """
        Overridable. Load the project's suites.
        """
        return load_suites_from_directory(osp.join(self.dir, "suites"))

    def load_fixtures(self):
        # type: () -> Sequence[Fixture]
        """
        Overridable. Load the project's fixtures.
        """
        fixtures_dir = osp.join(self.dir, "fixtures")
        if osp.exists(fixtures_dir):
            return load_fixtures_from_directory(fixtures_dir)
        else:
            return []

    def pre_run(self, cli_args, report_dir):
        # type: (Any, str) -> None
        """
        Overridable. This hook is called before running the tests.
        """
        pass

    def post_run(self, cli_args, report_dir):
        # type: (Any, str) -> None
        """
        Overridable. This hook is called after running the tests.
        """
        pass

    def build_report_title(self):
        # type: () -> Optional[str]
        """
        Overridable. Build a custom report title as a string.
        """
        return None

    def build_report_info(self):
        # type: () -> List[Tuple[str, str]]
        """
        Overridable. Build a list key/value pairs (expressed as a two items tuple)
        that will be available in the report.

        Example::

            [
                ("key1", "value1"),
                ("key2", "value2")
            ]
        """
        info = []
        if self.show_command_line_in_report:
            info.append(("Command line", " ".join([os.path.basename(sys.argv[0])] + sys.argv[1:])))
        return info


def _find_file_in_parent_directories(filename, dirname):
    if osp.exists(osp.join(dirname, filename)):
        return osp.join(dirname, filename)

    parent_dirname = osp.dirname(dirname)
    if parent_dirname == dirname:
        return None  # root directory has been reached

    return _find_file_in_parent_directories(filename, parent_dirname)


def find_project_file():
    # type: () -> Optional[str]
    filename = os.environ.get("LCC_PROJECT_FILE")
    if filename is not None:
        return filename if osp.exists(filename) else None

    return _find_file_in_parent_directories(PROJECT_CONFIG_FILE, os.getcwd())


def find_project_dir():
    # type: () -> Optional[str]
    project_filename = find_project_file()
    if project_filename is None:
        return None
    return osp.dirname(project_filename)


def create_project(project_dir):
    # type: (str) -> None
    shutil.copyfile(get_resource_path(("project", "template.py")), osp.join(project_dir, PROJECT_CONFIG_FILE))
    os.mkdir(osp.join(project_dir, "suites"))
    os.mkdir(osp.join(project_dir, "fixtures"))


def load_project_from_file(project_filename):
    # type: (str) -> Project

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
    # type: (str) -> Project
    return load_project_from_file(osp.join(project_dir, PROJECT_CONFIG_FILE))


def load_project():
    # type: () -> Project
    project_filename = find_project_file()
    if project_filename is None:
        raise ProjectError("Cannot find project file")

    return load_project_from_file(project_filename)
