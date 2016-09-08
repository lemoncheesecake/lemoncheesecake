'''
Created on Sep 8, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import LemonCheesecakeException

__all__ = "LoadTestError", "LoadTestSuiteError", "PropertyError", \
    "AbortTest", "AbortTestSuite", "AbortAllTests"

class LoadTestError(LemonCheesecakeException):
    message_prefix = "Cannot load test"

class LoadTestSuiteError(LemonCheesecakeException):
    message_prefix = "Cannot load testsuite"

class PropertyError(LemonCheesecakeException):
    message_prefix = "Property error"

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