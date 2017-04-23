'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import AbortTest

__all__ = ("log_match_result", "check_that", "require_that", "assert_that")

def log_match_result(hint, matcher, result, quiet=False):
    description = "Expect %s %s" % (hint, matcher.description())
    return get_runtime().check(
        description, result.outcome, str(result.description) if not quiet and result.description != None else None
    )

def check_that(hint, actual, matcher, quiet=False):
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    return result.outcome

def require_that(hint, actual, matcher, quiet=False):
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    if result.is_failure():
        raise AbortTest("previous requirement was not fulfilled")

def assert_that(hint, actual, matcher, quiet=False):
    result = matcher.matches(actual)
    if result.is_failure():
        log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")
