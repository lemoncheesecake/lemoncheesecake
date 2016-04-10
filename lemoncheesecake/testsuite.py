import fnmatch
import inspect

from lemoncheesecake.common import LemonCheesecakeException, LemonCheesecakeInternalError
from lemoncheesecake.runtime import get_runtime

###
# Shortcuts for tests
###

def debug(content):
    get_runtime().debug(content)

def info(content):
    get_runtime().info(content)

def warn(content):
    get_runtime().warn(content)

def error(content):
    get_runtime().error(content)

def step(description):
    get_runtime().step(description)

###
# Exception classes
###

class CannotLoadTest(LemonCheesecakeException):
    message_prefix = "Cannot load test"

class CannotLoadTestSuite(LemonCheesecakeException):
    message_prefix = "Cannot load testsuite"

class AbortTest(LemonCheesecakeException):
    pass

class AbortTestSuite(LemonCheesecakeException):
    pass

class AbortAllTests(LemonCheesecakeException):
    pass

###
# Test, TestSuite classes and decorators
###

FILTER_SUITE_MATCH = 0x1
FILTER_SUITE_MATCH_ID = 0x02
FILTER_SUITE_MATCH_DESCRIPTION = 0x04
FILTER_SUITE_MATCH_TAG = 0x08

class Filter:
    def __init__(self):
        self.test_id = []
        self.test_description = []
        self.testsuite_id = []
        self.testsuite_description = []
        self.tags = [ ]
    
    def is_empty(self):
        filters = self.test_id + self.testsuite_id + self.test_description + self.testsuite_description + self.tags
        return len(filters) == 0
    
    def match_test(self, test, parent_suite_match=0):
        match = False
        
        if self.test_id:
            for id in self.test_id:
                if fnmatch.fnmatch(test.id, id):
                    match = True
                    break
            if not match:
                return False
        
        if self.test_description:
            for desc in self.test_description:
                if fnmatch.fnmatch(test.description, desc):
                    match = True
                    break
            if not match:
                return False
        
        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(test.tags, tag):
                    match = True
                    break
            if not match:
                return False
        
        return True
    
    def match_testsuite(self, suite, parent_suite_match=0):
        match = 0
        
        if self.testsuite_id:
            for id in self.testsuite_id:
                if fnmatch.fnmatch(suite.id, id):
                    match |= FILTER_SUITE_MATCH_ID
                    break
            if not match & FILTER_SUITE_MATCH_ID:
                return 0
                
        if self.testsuite_description:
            for desc in self.testsuite_description:
                if fnmatch.fnmatch(suite.description, desc):
                    match |= FILTER_SUITE_MATCH_DESCRIPTION
                    break
            if not match & FILTER_SUITE_MATCH_DESCRIPTION:
                return 0

        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(suite.tags, tag):
                    match |= FILTER_SUITE_MATCH_TAG
                    break

        return match | FILTER_SUITE_MATCH

class Test:
    test_current_rank = 1

    def __init__(self, id, description, callback, force_rank=None):
        self.id = id
        self.description = description
        self.callback = callback
        self.tags = [ ]
        self.tickets = [ ]
        self.rank = force_rank if force_rank != None else Test.test_current_rank
        Test.test_current_rank += 1
        
    def __str__(self):
        return "%s (%s) # %d" % (self.id, self.description, self.rank)
        
class StaticTestDecorator:
    def __init__(self, description):
        self.description = description
    
    def __call__(self, callback):
        callback = callback
        id = callback.__name__
        
        return Test(id, self.description, callback)

def test(description): # decorator shortcut
    return StaticTestDecorator(description)

def tags(*tag_names):
    def wrapper(obj):
        if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
            raise LemonCheesecakeInternalError("Tags can only be added to Test and TestSuite objects (got %s)" % type(obj))
        obj.tags = tag_names
        return obj
    return wrapper

def tickets(*tickets):
    def wrapper(obj):
        if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
            raise LemonCheesecakeInternalError("Tickets can only be added to Test and TestSuite objects (got %s)" % type(obj))
        normalized_tickets = [ ]
        for ticket in tickets:
            if type(ticket) not in (tuple, list):
                ticket = [ ticket, None ] 
            normalized_tickets.append(ticket)
        obj.tickets = normalized_tickets
        return obj
    return wrapper

class TestSuite:
    tags = [ ]
    tickets = [ ]
    sub_testsuite_classes = [ ]        
    
    def load(self, parent_suite=None):
        self.parent_suite = parent_suite
        
        # suite id & description
        if not hasattr(self, "id"):
            self.id = self.__class__.__name__
        if not hasattr(self, "description"):
            self.description = self.__class__.__name__

        # static tests
        self._tests = [ ]
        for attr in dir(self):
            obj = getattr(self, attr)
            if isinstance(obj, Test):
                self.assert_test_description_is_unique(obj.description)
                self._tests.append(obj)
        self._tests = sorted(self._tests, key=lambda x: x.rank)

        # dynamic test        
        self.load_dynamic_tests()
        
        # sub testsuites
        self._sub_testsuites = [ ]
        for suite_class in self.sub_testsuite_classes:
            suite = suite_class()
            suite.load(self)
            self.assert_sub_test_suite_description_is_unique(suite.description)
            self._sub_testsuites.append(suite)
        
        # filtering data
        self._selected_test_ids = [ t.id for t in self._tests ]
    
    def get_path(self):
        suites = [ self ]
        parent_suite = self.parent_suite
        while parent_suite != None:
            suites.insert(0, parent_suite)
            parent_suite = parent_suite.parent_suite
        return suites
    
    def get_path_str(self, sep=">"):
        return (" %s " % sep).join([ s.id for s in self.get_path() ])
    
    def __str__(self):
        return self.get_path_str()
    
    def get_depth(self):
        depth = 1
        parent = self.parent_suite
        while parent:
            depth += 1
            parent = parent.parent_suite
        return depth
    
    def assert_test_description_is_unique(self, description):
        result = filter(lambda t: t.description == description, self._tests)
        if result:
            raise CannotLoadTest(
                "a test with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def assert_sub_test_suite_description_is_unique(self, description):
        result = filter(lambda s: s.description == description, self._sub_testsuites)
        if result:
            raise CannotLoadTestSuite(
                "a sub test suite with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def load_dynamic_tests(self):
        pass
    
    def get_tests(self, filtered=True):
        if filtered:
            return filter(lambda t: self.is_test_selected(t), self._tests)
        else:
            return self._tests
    
    def get_sub_testsuites(self, filtered=True):
        if filtered:
            return filter(lambda s: s.has_selected_tests(deep=True), self._sub_testsuites)
        else:
            return self._sub_testsuites
    
    def get_suite_id(self):
        return self.id
    
    def get_suite_description(self):
        return self.description
    
    def register_test(self, id, description, callback, before_test=None, after_test=None):
        if before_test and after_test:
            raise Exception("before_test and after_test are mutually exclusive")
        
        self.assert_test_description_is_unique(description)
        
        ref_test_id = before_test if before_test else after_test
        
        if ref_test_id:
            # find test corresponding to before_test/after_test
            ref_test, ref_test_idx = None, None
            for idx, test in enumerate(self._tests):
                if test.id == ref_test_id:
                    ref_test, ref_test_idx = test, idx
                    break
            if ref_test_idx == None:
                raise CannotLoadTest("Could not find any test named '%s' in the test suite '%s'" % (ref_test_id, self.get_suite_id()))
            
            # create test with the appropriate rank and shift all test's ranks coming after the new test
            new_test = Test(id, description, callback, force_rank=ref_test.rank + (1 if after_test else 0))
            for test in self._tests[ref_test_idx + (1 if after_test else 0):]:
                test.rank += 1
            self._tests.insert(ref_test_idx + (1 if after_test else 0), new_test)
        else:
            self._tests.append(Test(id, description, callback))
    
    ###
    # Filtering methods
    ###
    
    def apply_filter(self, filter, parent_suite_match=0):
        self._selected_test_ids = [ ]
        
        if parent_suite_match:
            suite_match = parent_suite_match
        else:
            suite_match = filter.match_testsuite(self)
                
        if suite_match:
            for test in self._tests:
                if filter.match_test(test, suite_match):
                    self._selected_test_ids.append(test.id)
        
        for suite in self._sub_testsuites:
            suite.apply_filter(filter, suite_match)

    def has_selected_tests(self, deep=True):
        if deep:
            if self._selected_test_ids:
                return True
             
            for suite in self._sub_testsuites:
                if suite.has_selected_tests():
                    return True
             
            return False
        else:
            return bool(self._selected_test_ids)
    
    def is_test_selected(self, test):
        return test.id in self._selected_test_ids
    
    ###
    # Hooks
    ###
    
    def before_suite(self):
        pass
    
    def after_suite(self):
        pass

    def before_test(self, test_name):
        pass
    
    def after_test(self, test_name):
        pass