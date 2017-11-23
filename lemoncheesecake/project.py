'''
Created on Dec 10, 2016

@author: nicolas
'''

import os
import os.path as osp
import shutil

from lemoncheesecake.suite import load_suites_from_directory
from lemoncheesecake.fixtures import load_fixtures_from_directory
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.reporting import ConsoleBackend, HtmlBackend, JsonBackend, XmlBackend, JunitBackend,\
    filter_available_reporting_backends
from lemoncheesecake.reporting.reportdir import report_dir_with_archiving, archive_dirname_datetime
from lemoncheesecake.exceptions import ProjectError, UserError, serialize_current_exception
from lemoncheesecake.utils import get_resource_path
from lemoncheesecake.importer import import_module

PROJECT_CONFIG_FILE = "project.py"


class HasCustomCliArgs:
    """"Mixin class for project configuration with custom CLI args"""
    def add_custom_cli_args(self, cli_parser):
        """Setup custom CLI args in cli_parser"""
        pass


class HasPreRunHook:
    """Mixin class for project configuration that requires code to be executed before tests"""
    def pre_run(self, report_dir):
        """Pre-run hook"""
        pass


class HasPostRunHook:
    """Mixin class for project configuration that requires code to be executed after tests"""
    def post_run(self, report_dir):
        """Post-run hook"""
        pass


class HasMetadataPolicy:
    """Mixin class project configuration that a metadata policy"""
    def get_metadata_policy(self):
        """Return a `lemoncheesecake.validators.MetadataPolicy` instance"""
        return MetadataPolicy()


class ProjectConfiguration:
    """Abstract class for project configuration"""

    def get_suites(self):
        """Return a list of `lemoncheesecake.suite.Suite` instances"""
        raise NotImplementedError()
    
    def get_fixtures(self):
        """Return a list of `lemoncheesecake.fixtures.Fixture` instances"""
        return []
    
    def get_all_reporting_backends(self):
        """Return a list of `lemoncheesecake.reporting.ReportingBackend` instances supported by the project"""
        raise NotImplementedError()
    
    def get_default_reporting_backends_for_test_run(self):
        """Return a list of `lemoncheesecake.reporting.ReportingBackend` that will used by default by lcc run"""
        raise NotImplementedError()

    def create_report_dir(self, top_dir):
        """Create a new report directory within `top_dir` (in case the user does not provide a custom report directory)"""
        raise NotImplementedError()

    def get_report_title(self):
        """Return the report title"""
        return None

    def get_report_info(self):
        """Return a list of key/value tuple to be added to report info"""
        return []


class SimpleProjectConfiguration(ProjectConfiguration):
    def __init__(self, suites_dir, fixtures_dir=None, report_title=None):
        self._suites_dir = suites_dir
        self._fixtures_dir = fixtures_dir
        self._report_title = report_title
        self.console_backend = ConsoleBackend()
        self.json_backend = JsonBackend()
        self.xml_backend = XmlBackend()
        self.junit_backend = JunitBackend()
        self.html_backend = HtmlBackend()
    
    def get_suites(self):
        return load_suites_from_directory(self._suites_dir)
    
    def get_fixtures(self):
        return load_fixtures_from_directory(self._fixtures_dir) if self._fixtures_dir else []

    def get_report_title(self):
        return self._report_title
    
    def get_all_reporting_backends(self):
        return [self.console_backend, self.json_backend, self.html_backend, self.xml_backend, self.junit_backend]

    def get_default_reporting_backends_for_test_run(self):
        return [self.console_backend, self.json_backend, self.html_backend]
    
    def create_report_dir(self, top_dir):
        return report_dir_with_archiving(top_dir, archive_dirname_datetime)


class Project:
    def __init__(self, project_config, project_dir):
        self._config = project_config
        self._project_dir = project_dir

    def get_project_dir(self):
        return self._project_dir

    def add_custom_args_to_run_cli(self, cli_args_parser):
        if isinstance(self._config, HasCustomCliArgs):
            cli_group = cli_args_parser.add_argument_group("Project custom options")
            self._config.add_custom_cli_args(cli_group)

    def create_report_dir(self):
        return self._config.create_report_dir(self._project_dir)

    def get_suites(self, check_metadata_policy=True):
        suites = self._config.get_suites()
        if check_metadata_policy and isinstance(self._config, HasMetadataPolicy):
            policy = self._config.get_metadata_policy()
            policy.check_suites_compliance(suites)
        return suites

    def get_fixtures(self):
        return self._config.get_fixtures()

    def get_all_reporting_backends(self):
        return filter_available_reporting_backends(self._config.get_all_reporting_backends())

    def get_default_reporting_backends_for_test_run(self):
        return filter_available_reporting_backends(self._config.get_default_reporting_backends_for_test_run())

    def run_pre_session_hook(self, report_dir):
        if isinstance(self._config, HasPreRunHook):
            self._config.pre_run(report_dir)

    def run_post_session_hook(self, report_dir):
        if isinstance(self._config, HasPostRunHook):
            self._config.post_run(report_dir)

    def on_tests_beginning(self, report):
        title = self._config.get_report_title()
        if title is not None:
            report.title = self._config.get_report_title()

        for key, value in self._config.get_report_info():
            report.add_info(key, value)


def _find_file_in_parent_directories(filename, dirname):
    if osp.exists(osp.join(dirname, filename)):
        return osp.join(dirname, filename)

    parent_dirname = osp.dirname(dirname)
    if parent_dirname == dirname:
        return None # root directory has been reached

    return _find_file_in_parent_directories(filename, parent_dirname)


def find_project_file():
    filename = os.environ.get("LCC_PROJECT_FILE")
    if filename is not None:
        return filename if osp.exists(filename) else None

    filename = _find_file_in_parent_directories(PROJECT_CONFIG_FILE, os.getcwd())
    return filename # filename can be None


def create_project(project_dir):
    shutil.copyfile(get_resource_path(osp.join("project", "template.py")), osp.join(project_dir, PROJECT_CONFIG_FILE))
    os.mkdir(osp.join(project_dir, "suites"))
    os.mkdir(osp.join(project_dir, "fixtures"))


def load_project_from_file(project_filename):
    project_dir = osp.dirname(project_filename)

    # load project module
    try:
        project_config_module = import_module(project_filename)
    except UserError as e:
        raise e # propagate UserError
    except Exception:
        raise ProjectError("Got an unexpected error while loading project:%s" % (
            serialize_current_exception()
        ))
    
    # get project config instance
    try:
        project_config = project_config_module.project
    except AttributeError:
        raise ProjectError("Cannot find symbol 'project' in module '%s'" % project_filename)
    if not isinstance(project_config, ProjectConfiguration):
        raise ProjectError("Symbol 'project' in module '%s' does not inherit lemoncheesecake.project.ProjectConfiguration" % project_filename)
    
    return Project(project_config, project_dir)


def load_project_from_dir(project_dir):
    return load_project_from_file(osp.join(project_dir, PROJECT_CONFIG_FILE))


def load_project():
    project_filename = find_project_file()
    if project_filename is None:
        raise ProjectError("Cannot find project file")

    return load_project_from_file(project_filename)
