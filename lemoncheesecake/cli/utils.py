'''
Created on Mar 12, 2017

@author: nicolas
'''

from __future__ import print_function

import os.path as osp
import sys
import platform

import lemoncheesecake
from lemoncheesecake.project import load_project
from lemoncheesecake.reporting import get_reporting_backends
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.testtree import filter_suites
from lemoncheesecake.exceptions import UserError, ProjectNotFound

LEMONCHEESECAKE_VERSION = "lemoncheesecake version %s (using Python %s - %s)" % (
    lemoncheesecake.__version__, platform.python_version(), sys.executable
)


def load_suites_from_project(project, test_filter=None):
    suites = project.load_suites()
    if all(suite.is_empty() for suite in suites):
        raise UserError("No test is defined in your lemoncheesecake project.")

    project.metadata_policy.check_suites_compliance(suites)

    if test_filter:
        suites = filter_suites(suites, test_filter)
        if len(suites) == 0:
            raise UserError("The filter does not match any test")

    return suites


def auto_detect_reporting_backends():
    try:
        project = load_project()
        return project.reporting_backends.values()
    except ProjectNotFound:
        return get_reporting_backends()


def add_report_path_cli_arg(cli_parser):
    cli_parser.add_argument("report_path", nargs='?', help="Report file or directory")


def get_report_path(cli_args):
    # first attempt: has the report path been specified on the CLI ?
    if cli_args.report_path:
        return cli_args.report_path

    # second attempt: is there a report on the current working directory ?
    if osp.exists(DEFAULT_REPORT_DIR_NAME):
        return DEFAULT_REPORT_DIR_NAME

    # third attempt: try to find a project and then the corresponding report
    try:
        project = load_project()
    except ProjectNotFound:
        pass
    else:
        report_path = osp.join(project.dir, DEFAULT_REPORT_DIR_NAME)
        if osp.exists(report_path):
            return report_path

    # could not find anything
    raise UserError("Cannot find report path")
