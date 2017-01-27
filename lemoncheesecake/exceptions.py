'''
Created on Sep 8, 2016

@author: nicolas
'''

class LemonCheesecakeException(Exception):
    message_prefix = None
    
    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s, %s" % (self.message_prefix, s)
        return s

class LemonCheesecakeInternalError(LemonCheesecakeException):
    message_prefix = "internal error"

class ProgrammingError(LemonCheesecakeException):
    message_prefix = "programing error"

class ProjectError(LemonCheesecakeException):
    pass

class MethodNotImplemented(ProgrammingError):
    def __init__(self, obj, method_name):
        ProgrammingError.__init__(self, "Class '%s' must implement the method '%s'" % (obj.__class__._name__, method_name))

class ImportTestSuiteError(LemonCheesecakeException):
    message_prefix = "cannot import testsuite"

class FixtureError(LemonCheesecakeException):
    pass

class InvalidMetadataError(ProgrammingError):
    message_prefix = "invalid metadata"

class UnknownReportBackendError(LemonCheesecakeException):
    message_prefix = "unknown report backend"

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
