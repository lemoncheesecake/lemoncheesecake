'''
Created on Mar 12, 2017

@author: nicolas
'''

from __future__ import print_function

import os.path as osp
import sys
import platform

import lemoncheesecake
from lemoncheesecake.project import find_project_dir, find_project_file, load_project_from_file
from lemoncheesecake.reporting import get_reporting_backends
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.filter import filter_suites
from lemoncheesecake.exceptions import UserError, ProjectError

LEMONCHEESECAKE_VERSION = "lemoncheesecake version %s (using Python %s - %s)" % (
    lemoncheesecake.__version__, platform.python_version(), sys.executable
)


def load_suites_from_project(project, filtr=None):
    suites = project.load_suites()
    if all(suite.is_empty() for suite in suites):
        raise UserError("No test is defined in your lemoncheesecake project.")

    project.metadata_policy.check_suites_compliance(suites)

    if filtr:
        suites = filter_suites(suites, filtr)
        if len(suites) == 0:
            raise UserError("The filter does not match any test")

    return suites


def auto_detect_reporting_backends():
    project_filename = find_project_file()
    if project_filename is None:
        return get_reporting_backends()

    try:
        project = load_project_from_file(project_filename)
        return project.reporting_backends.values()
    except ProjectError:
        return get_reporting_backends()


def add_report_path_cli_arg(cli_parser):
    cli_parser.add_argument("report_path", nargs='?', help="Report file or directory")


def get_report_path(cli_args):
    if cli_args.report_path is None:
        project_dirname = find_project_dir()
        if project_dirname is None:
            raise UserError("Cannot find project")
        return osp.join(project_dirname, DEFAULT_REPORT_DIR_NAME)
    else:
        return cli_args.report_path
