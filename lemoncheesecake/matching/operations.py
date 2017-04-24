'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import AbortTest

__all__ = ("log_match_result", "check_that", "require_that", "assert_that")

def log_match_result(hint, matcher, result, quiet=False):
    """Add a check log to the report.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    description = "Expect %s %s" % (hint, matcher.description())
    return get_runtime().check(
        description, result.outcome, str(result.description) if not quiet and result.description != None else None
    )

def check_that(hint, actual, matcher, quiet=False):
    """Check that actual matches given matcher.
    
    A check log is added to the report.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    return result.outcome

def require_that(hint, actual, matcher, quiet=False):
    """Require that actual matches given matcher.
    
    A check log is added to the report. An AbortTest exception is raised if the check does not succeed.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    if result.is_failure():
        raise AbortTest("previous requirement was not fulfilled")

def assert_that(hint, actual, matcher, quiet=False):
    """Assert that actual matches given matcher.
    
    If assertion fail, a check log is added to the report and an AbortTest exception is raised.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    result = matcher.matches(actual)
    if result.is_failure():
        log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")
