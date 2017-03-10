'''
Created on Feb 17, 2017

@author: nicolas
'''

from __future__ import print_function

from termcolor import colored
from terminaltables import AsciiTable

from lemoncheesecake.testsuite import get_filter_from_cli_args, filter_testsuites
from lemoncheesecake.exceptions import UserError

def bold(s):
    return colored(s, attrs=["bold"])

def print_table(title, headers, lines):
    if lines:
        print("%s:" % title)
        print(AsciiTable([headers] + lines).table)
    else:
        print("%s: <none>" % title)
    print()

def filter_testsuites_from_cli_args(suites, cli_args):
    if not any(suite.has_selected_tests() for suite in suites):
        raise UserError("No test is defined in your lemoncheesecake project.")
    
    filtr = get_filter_from_cli_args(cli_args)
    if not filtr.is_empty():
        suites = filter_testsuites(suites, filtr)
        if len(suites) == 0:
            raise UserError("The filter does not match any test")
    return suites
