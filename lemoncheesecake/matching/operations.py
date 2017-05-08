'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import AbortTest
from lemoncheesecake.matching.matchers.dict import HasEntry
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "log_match_result",
    "check_that", "check_that_entry",
    "require_that", "require_that_entry",
    "assert_that", "assert_that_entry"
)

class _HasEntry(HasEntry):
    def description(self):
        ret = 'entry "%s"' % self.key
        if self.value_matcher:
            ret += " " + self.value_matcher.description()
        return ret

def _entry_operation(operation):
    def wrapper(key, actual, matcher=None, quiet=False):
        return operation(
            "", actual, _HasEntry(key, matcher if matcher != None else is_(matcher)), quiet=quiet
        )
    wrapper.__doc__ = "Same as %s but takes dict key as first argument instead of hint." % operation.__name__
    return wrapper

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

check_that_entry = _entry_operation(check_that)

def require_that(hint, actual, matcher, quiet=False):
    """Require that actual matches given matcher.
    
    A check log is added to the report. An AbortTest exception is raised if the check does not succeed.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    if result.is_failure():
        raise AbortTest("previous requirement was not fulfilled")

require_that_entry = _entry_operation(require_that)

def assert_that(hint, actual, matcher, quiet=False):
    """Assert that actual matches given matcher.
    
    If assertion fail, a check log is added to the report and an AbortTest exception is raised.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    result = matcher.matches(actual)
    if result.is_failure():
        log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")

assert_that_entry = _entry_operation(assert_that)
