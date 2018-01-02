'''
Created on Mar 12, 2017

@author: nicolas
'''

from __future__ import print_function

import lemoncheesecake
from lemoncheesecake.project import find_project_file, load_project_from_file
from lemoncheesecake.reporting import get_available_backends
from lemoncheesecake.filter import make_run_filter, filter_suites
from lemoncheesecake.exceptions import UserError, ProjectError

LEMONCHEESECAKE_VERSION = "lemoncheesecake version %s" % lemoncheesecake.__version__


def filter_suites_from_cli_args(suites, cli_args):
    filtr = make_run_filter(cli_args)
    if filtr.is_empty():
        return suites

    suites = filter_suites(suites, filtr)
    if len(suites) == 0:
        raise UserError("The filter does not match any test")

    return suites


def get_suites_from_project(project, cli_args):
    suites = project.get_suites()
    if all(suite.is_empty() for suite in suites):
        raise UserError("No test is defined in your lemoncheesecake project.")

    return filter_suites_from_cli_args(suites, cli_args)


def auto_detect_reporting_backends():
    project_filename = find_project_file()
    if project_filename is None:
        return get_available_backends()

    try:
        project = load_project_from_file(project_filename)
        return project.get_all_reporting_backends()
    except ProjectError:
        return get_available_backends()
