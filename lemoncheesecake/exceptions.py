'''
Created on Sep 8, 2016

@author: nicolas
'''

class LemonCheesecakeException(Exception):
    message_prefix = None
    
    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s: %s" % (self.message_prefix, s)
        return s

class LemonCheesecakeInternalError(LemonCheesecakeException):
    message_prefix = "Internal error"

class ProgrammingError(LemonCheesecakeException):
    message_prefix = "Programing error"

class ProjectError(LemonCheesecakeException):
    def __init__(self, project_file=None, reason=None):
        self.project_file = project_file
        self.reason = reason
    
    def __str__(self):
        if self.project_file:
            error = "Cannot load project file '%s'" % self.project_file
        else:
            error = "Cannot load project"
        if self.reason:
            error += ": %s" % self.reason
        return error

class MethodNotImplemented(ProgrammingError):
    def __init__(self, obj, method_name):
        ProgrammingError.__init__(self, "Class '%s' must implement the method '%s'" % (obj.__class__._name__, method_name))

class ImportTestSuiteError(LemonCheesecakeException):
    message_prefix = "Cannot import testsuite"

class InvalidMetadataError(ProgrammingError):
    message_prefix = "Invalid metadata"

class UnknownReportBackendError(LemonCheesecakeException):
    message_prefix = "Unknown report backend"

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
