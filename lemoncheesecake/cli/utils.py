'''
Created on Mar 12, 2017

@author: nicolas
'''

from __future__ import print_function

import lemoncheesecake
from lemoncheesecake.filter import make_filter_from_cli_args, filter_suites
from lemoncheesecake.exceptions import UserError

LEMONCHEESECAKE_VERSION = "lemoncheesecake version %s" % lemoncheesecake.__version__


def filter_suites_from_cli_args(suites, cli_args):
    filtr = make_filter_from_cli_args(cli_args)
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
