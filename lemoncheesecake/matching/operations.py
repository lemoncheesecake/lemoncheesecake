'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.exceptions import AbortTest, ProgrammingError
from lemoncheesecake.matching.matchers.dict import HasEntry, wrap_key_matcher
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "log_match_result",
    "check_that", "check_that_entry",
    "require_that", "require_that_entry",
    "assert_that", "assert_that_entry",
    "this_dict"
)

class _HasEntry(HasEntry):
    def description(self):
        ret = 'entry %s' % self.key_matcher.description()
        if self.value_matcher:
            ret += " " + self.value_matcher.description()
        return ret

class DictContext:
    def __init__(self, actual, base_key):
        self.actual = actual
        self.base_key = base_key

class ThisDict():
    _contexts = []
    
    def __init__(self, actual):
        self.context = DictContext(actual, [])
    
    def using_base_key(self, base_key):
        self.context.base_key = base_key if type(base_key) in (list, tuple) else [base_key]
        return self
    
    def __enter__(self):
        self._contexts.append(self.context)
        return self.context.actual
    
    def __exit__(self, type_, value, traceback):
        self._contexts.pop()
    
    @staticmethod
    def get_current_context():
        try:
            return ThisDict._contexts[-1]
        except IndexError:
            return None

def this_dict(actual):
    """
    Set actual to be used as implict dict in *_that_entry functions when used
    within a 'with' statement.
    """
    return ThisDict(actual)

def _entry_operation(operation):
    def wrapper(key_matcher, value_matcher=None, in_=None, quiet=False):
        actual = in_
        base_key = []
        if not actual:
            context = ThisDict.get_current_context()
            if not context:
                raise ProgrammingError("Actual dict must be set either using in_ argument or using 'with this_dict(...)' statement")
            actual = context.actual
            base_key = context.base_key
        matcher = _HasEntry(
            wrap_key_matcher(key_matcher, base_key=base_key),
            value_matcher if value_matcher != None else is_(value_matcher)
        )
        return operation("", actual, matcher, quiet=quiet)
    wrapper.__doc__ = "Helper function for %s, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement" % \
        operation.__name__
    return wrapper

def log_match_result(hint, matcher, result, quiet=False):
    """Add a check log to the report.
    
    If quiet is set to True, the check details won't appear in the check log. 
    """
    description = "Expect %s %s" % (hint, matcher.description())
    return get_runtime().check(
        description, result.outcome, result.description if not quiet and result.description != None else None
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
