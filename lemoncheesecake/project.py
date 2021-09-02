'''
Created on Dec 10, 2016

@author: nicolas
'''

import sys
import os
import os.path as osp
import shutil
import argparse
import inspect

from typing import Any, Dict, Optional, Sequence, Tuple, List

from lemoncheesecake.session import Session
from lemoncheesecake.events import AsyncEventManager
from lemoncheesecake.suite import load_suites_from_directory, Suite
from lemoncheesecake.runner import run_suites
from lemoncheesecake.fixture import load_fixtures_from_directory, Fixture, FixtureRegistry, BuiltinFixture
from lemoncheesecake.metadatapolicy import MetadataPolicy
from lemoncheesecake.reporting import get_reporting_backends, ReportingBackend
from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation
from lemoncheesecake.exceptions import ProjectLoadingError, ProjectNotFound, ModuleImportError
from lemoncheesecake.helpers.resources import get_resource_path
from lemoncheesecake.helpers.moduleimport import import_module
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.exceptions import UserError, LemoncheesecakeException, serialize_current_exception

PROJECT_FILE = "project.py"
DEFAULT_REPORTING_BACKENDS = ("console", "json", "html")
DEFAULT_SUITES_DIR = "suites"
DEFAULT_FIXTURES_DIR = "fixtures"


def get_caller_dir(stack):
    frame_info = stack[1]
    return os.path.dirname(frame_info[1])


class Project(object):
    def __init__(self, project_dir=None):
        #: The project's directory path (optional, defaults to the caller dir)
        self.dir = project_dir or get_caller_dir(inspect.stack())  # type: str
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
        return load_suites_from_directory(osp.join(self.dir, DEFAULT_SUITES_DIR))

    def load_fixtures(self):
        # type: () -> Sequence[Fixture]
        """
        Overridable. Load the project's fixtures.
        """
        fixtures_dir = osp.join(self.dir, DEFAULT_FIXTURES_DIR)
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


def create_project(project_dir):
    # type: (str) -> None
    shutil.copyfile(get_resource_path(("project", "template.py")), osp.join(project_dir, PROJECT_FILE))
    os.mkdir(osp.join(project_dir, "suites"))
    os.mkdir(osp.join(project_dir, "fixtures"))


def _load_project_from_file(project_filename):
    # type: (str) -> Project

    # load project module
    try:
        project_module = import_module(project_filename)
    except ModuleImportError as e:
        raise ProjectLoadingError(str(e))

    # get project config instance
    try:
        project = project_module.project
    except AttributeError:
        raise ProjectLoadingError("Cannot find symbol 'project' in module '%s'" % project_filename)
    if not isinstance(project, Project):
        raise ProjectLoadingError("Symbol 'project' in module '%s' does not inherit lemoncheesecake.project.Project" % project_filename)
    
    return project


def _iter_on_path_hierarchy(path):
    yield path
    parent_path = osp.dirname(path)
    while parent_path != path:
        yield parent_path
        path, parent_path = parent_path, osp.dirname(parent_path)


def _load_project_from_path(path):
    if osp.isfile(path):
        return _load_project_from_file(path)
    elif osp.isdir(path):
        if osp.exists(osp.join(path, PROJECT_FILE)):
            return _load_project_from_file(osp.join(path, PROJECT_FILE))
        if osp.exists(osp.join(path, DEFAULT_SUITES_DIR)):
            return Project(path)

    raise ProjectLoadingError("'%s' is not a suitable project path" % path)


def load_project(path=None):
    # type: (str) -> Project

    # first try: from argument
    if path:
        return _load_project_from_path(path)

    # second try: from environment
    path = os.environ.get("LCC_PROJECT", os.environ.get("LCC_PROJECT_FILE"))
    if path:
        return _load_project_from_path(path)

    # third try: look for a project.py file in directory hierarchy
    for dirname in _iter_on_path_hierarchy(os.getcwd()):
        filename = osp.join(dirname, PROJECT_FILE)
        if osp.exists(filename):
            return _load_project_from_file(filename)

    # fourth try: look for a "suites" sub-directory in the directory hierarchy
    for dirname in _iter_on_path_hierarchy(os.getcwd()):
        if osp.exists(osp.join(dirname, DEFAULT_SUITES_DIR)):
            return Project(dirname)

    # no luck
    raise ProjectNotFound("Cannot neither find a 'suites' directory nor a 'project.py' file")


def _build_fixture_registry(project, cli_args):
    registry = FixtureRegistry()
    registry.add_fixture(BuiltinFixture("cli_args", cli_args))
    registry.add_fixture(BuiltinFixture("project_dir", project.dir))
    for fixture in project.load_fixtures():
        registry.add_fixture(fixture)
    registry.check_dependencies()
    return registry


def _setup_report_from_project(report, project):
    try:
        title = project.build_report_title()
    except Exception:
        raise LemoncheesecakeException(
            "Got an unexpected exception while getting report title from project:%s" % \
                serialize_current_exception(show_stacktrace=True)
        )
    if title:
        report.title = title

    try:
        info = list(project.build_report_info())
    except Exception:
        raise LemoncheesecakeException(
            "Got an unexpected exception while getting report info from project:%s" % \
                serialize_current_exception(show_stacktrace=True)
        )

    for key, value in info:
        report.add_info(key, value)


def run_project(project, suites, cli_args, reporting_backends, report_dir, report_saving_strategy,
                force_disabled=False, stop_on_failure=False, nb_threads=1):
    # Build fixture registry
    fixture_registry = _build_fixture_registry(project, cli_args)
    fixture_registry.check_fixtures_in_suites(suites)

    # Handle "pre_run" hook
    try:
        project.pre_run(cli_args, report_dir)
    except UserError as e:
        raise e
    except Exception:
        raise LemoncheesecakeException(
            "Got an unexpected exception while running project's pre_run method:%s" % \
                serialize_current_exception(show_stacktrace=True)
        )

    # Create session
    session = Session.create(
        AsyncEventManager.load(), reporting_backends, report_dir, report_saving_strategy,
        nb_threads=nb_threads, parallelized=nb_threads > 1 and len(list(flatten_tests(suites))) > 1
    )
    _setup_report_from_project(session.report, project)

    # Run tests
    run_suites(
        suites, fixture_registry, session,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        nb_threads=nb_threads
    )

    # Handle "post_run" hook
    try:
        project.post_run(cli_args, report_dir)
    except UserError as e:
        raise e
    except Exception:
        raise LemoncheesecakeException(
            "Got an unexpected exception while running project's post_run method:%s" % \
                serialize_current_exception(show_stacktrace=True)
        )

    return session.report
