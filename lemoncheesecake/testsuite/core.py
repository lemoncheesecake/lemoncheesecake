'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import InvalidMetadataError, ProgrammingError

__all__ = "TestSuite", "Test"

class Test:
    test_current_rank = 1

    def __init__(self, id, description, callback, force_rank=None):
        self.id = id
        self.description = description
        self.callback = callback
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
        self.rank = force_rank if force_rank != None else Test.test_current_rank
        Test.test_current_rank += 1
        
    def __str__(self):
        return "%s (%s) # %d" % (self.id, self.description, self.rank)
        
class TestSuite:
    tags = [ ]
    properties = {}
    links = [ ]
    sub_suites = [ ]        
    
    def load(self, parent_suite=None):
        self.parent_suite = parent_suite
        
        # suite id & description
        if not hasattr(self, "id"):
            self.id = self.__class__.__name__
        if not hasattr(self, "description"):
            self.description = self.id

        # static tests
        self._tests = [ ]
        for attr in dir(self):
            obj = getattr(self, attr)
            if isinstance(obj, Test):
                self.assert_test_description_is_unique(obj.description)
                self._tests.append(obj)
        self._tests = sorted(self._tests, key=lambda x: x.rank)

        # dynamic test        
        self.load_generated_tests()
        
        # find sub testsuite classes
        # - first: in the "sub_suites" attribute of the class
        suite_classes = self.sub_suites[:]
        # - second: in inline attributes
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if inspect.isclass(attr) and issubclass(attr, TestSuite): 
                suite_classes.append(attr) 
        
        # load sub testsuites
        self._sub_testsuites = [ ]
        for suite_class in suite_classes:
            sub_suite = suite_class()
            sub_suite.load(self)
            self.assert_sub_test_suite_description_is_unique(sub_suite.description)
            self._sub_testsuites.append(sub_suite)

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
        result = list(filter(lambda t: t.description == description, self._tests))
        if result:
            raise InvalidMetadataError(
                "a test with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def assert_sub_test_suite_description_is_unique(self, description):
        result = list(filter(lambda s: s.description == description, self._sub_testsuites))
        if result:
            raise InvalidMetadataError(
                "a sub test suite with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def load_generated_tests(self):
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
    
    def register_test(self, new_test, before_test=None, after_test=None):
        if before_test and after_test:
            raise ProgrammingError("before_test and after_test are mutually exclusive")
        
        self.assert_test_description_is_unique(new_test.description)
        
        ref_test_id = before_test if before_test else after_test
        
        if ref_test_id:
            # find test corresponding to before_test/after_test
            ref_test, ref_test_idx = None, None
            for idx, test in enumerate(self._tests):
                if test.id == ref_test_id:
                    ref_test, ref_test_idx = test, idx
                    break
            if ref_test_idx == None:
                raise InvalidMetadataError("Could not find any test named '%s' in the test suite '%s'" % (ref_test_id, self.get_suite_id()))
            
            # set the test appropriate rank and shift all test's ranks coming after the new test
            new_test.rank = ref_test.rank + (1 if after_test else 0)
            for test in self._tests[ref_test_idx + (1 if after_test else 0):]:
                test.rank += 1
            self._tests.insert(ref_test_idx + (1 if after_test else 0), new_test)
        else:
            self._tests.append(new_test)
    
    def register_tests(self, tests, before_test=None, after_test=None):
        if before_test and after_test:
            raise ProgrammingError("before_test and after_test are mutually exclusive")
        
        if after_test:
            previous_test = after_test
            for test in tests:
                self.register_test(test, after_test=previous_test)
                previous_test = test.id
        else:
            for test in tests:
                self.register_test(test, before_test=before_test)
    
    ###
    # Filtering methods
    ###
    
    def apply_filter(self, filter, parent_suite_match=0):
        self._selected_test_ids = [ ]
        
        suite_match = filter.match_testsuite(self, parent_suite_match)
        suite_match |= parent_suite_match
        
        if suite_match & filter.get_flags_to_match_testsuite() == filter.get_flags_to_match_testsuite():
            for test in self._tests:
                test_match = filter.match_test(test, suite_match)
                if test_match:
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
        """Hook method called before running the tests (and sub testsuites) of the testsuite"""
        pass
    
    def after_suite(self):
        """Hook method called after running the tests (and sub testsuites) of the testsuite"""
        pass

    def before_test(self, test_name):
        """Hook method called before running each test of the testsuite"""
        pass
    
    def after_test(self, test_name):
        """Hook method called after running each test of the testsuite"""
        pass
