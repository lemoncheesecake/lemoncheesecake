'''
Created on Sep 8, 2016

@author: nicolas
'''

import sys
import traceback

class LemonCheesecakeException(Exception):
    message_prefix = None

    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s, %s" % (self.message_prefix, s)
        return s

class LemonCheesecakeInternalError(LemonCheesecakeException):
    pass
InternalError = LemonCheesecakeInternalError

class ProgrammingError(LemonCheesecakeException):
    pass

class ProjectError(LemonCheesecakeException):
    pass

class MethodNotImplemented(ProgrammingError):
    def __init__(self, obj, method_name):
        ProgrammingError.__init__(self, "Class '%s' must implement the method '%s'" % (obj.__class__.__name__, method_name))

def method_not_implemented(method_name, obj):
    raise MethodNotImplemented(obj, method_name)

class ImportTestSuiteError(LemonCheesecakeException):
    pass

class ImportFixtureError(LemonCheesecakeException):
    pass

class FixtureError(LemonCheesecakeException):
    pass

class InvalidMetadataError(ProgrammingError):
    pass

class UnknownReportBackendError(LemonCheesecakeException):
    pass

class AbortTest(LemonCheesecakeException):
    message_prefix = "The test has been aborted"

    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)

class AbortTestSuite(LemonCheesecakeException):
    message_prefix = "The testsuite has been aborted"

    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)

class AbortAllTests(LemonCheesecakeException):
    message_prefix = "All tests have been aborted"

    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)

class UserError(LemonCheesecakeException):
    pass

class InvalidReportFile(LemonCheesecakeException):
    pass

def serialize_current_exception(show_stacktrace=True):
    if show_stacktrace:
        return "\n" + "<" * 72 + "\n" + traceback.format_exc() + ">" * 72
    else:
        return " " + str(sys.exc_info()[1])
