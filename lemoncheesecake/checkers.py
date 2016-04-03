'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime

def check(description, outcome, details=None):
    return get_runtime().check(description, outcome, details)

def check_eq(name, actual, expected):
    outcome = actual == expected
    description = "Expected '%s' to be equal to '%s' (type %s)" % (name, expected, type(expected))
    details = None
    if not outcome:
        details = "Got '%s' (type %s)" % (actual, type(actual))
    return check(description, outcome, details)