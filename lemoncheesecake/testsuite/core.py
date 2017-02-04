'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import InvalidMetadataError, ProgrammingError
from lemoncheesecake.utils import dict_cat, object_has_method, get_distincts_in_list

__all__ = "TestSuite", "Test"

class Metadata:
    _next_rank = 1
    
    def __init__(self):
        self.is_test = False
        self.is_testsuite = False
        self.name = None
        self.description = None
        self.properties = {}
        self.tags = []
        self.links = []
        self.rank = None

def get_metadata_next_rank():
    rank = Metadata._next_rank
    Metadata._next_rank += 1
    return rank

class Test:
    def __init__(self, name, description, callback):
        self.name = name
        self.description = description
        self.callback = callback
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]
    
    def get_params(self):
        return inspect.getargspec(self.callback).args[1:]

class TestSuite:
    def __init__(self, name, description, parent_suite=None):
        self.parent_suite = None
        self.name = name
        self.description = description
        self.tags = []
        self.properties = {}
        self.links = []
        self._hooks = {}
        self._tests = []
        self._sub_testsuites = []
        self._selected_test_names = []
    
    def add_hook(self, hook_name, func):
        self._hooks[hook_name] = func
    
    def has_hook(self, hook_name):
        return hook_name in self._hooks
    
    def get_hook(self, hook_name):
        return self._hooks.get(hook_name)
            
    def get_path(self):
        suites = [ self ]
        parent_suite = self.parent_suite
        while parent_suite != None:
            suites.insert(0, parent_suite)
            parent_suite = parent_suite.parent_suite
        return suites
    
    def get_path_str(self, sep="."):
        return sep.join([s.name for s in self.get_path()])
    
    def get_test_path_str(self, test, sep="."):
        return self.get_path_str(sep=sep) + sep + test.name
    
    def __str__(self):
        return self.get_path_str()
    
    def get_depth(self):
        depth = 1
        parent = self.parent_suite
        while parent:
            depth += 1
            parent = parent.parent_suite
        return depth
    
    def assert_test_is_unique_in_suite(self, test):
        try:
            next(t for t in self._tests if t.description == test.description)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "a test with description '%s' is already registered in test suite %s" % (test.description, self.get_path_str())
            )
        
        try:
            next(t for t in self._tests if t.name == test.name)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "a test with name '%s' is already registered in test suite %s" % (test.name, self.get_path_str())
            )
        
    def assert_sub_suite_is_unique_in_suite(self, sub_suite):
        try:
            next(s for s in self._sub_testsuites if s.description == sub_suite.description)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "a sub test suite with description '%s' is already registered in test suite %s" % (sub_suite.name, self.get_path_str())
            )
        
        try:
            next(s for s in self._sub_testsuites if s.name == sub_suite.name)
        except StopIteration:
            pass
        else:
            raise InvalidMetadataError(
                "a sub test suite with name '%s' is already registered in test suite %s" % (sub_suite.name, self.get_path_str())
            )
    
    def add_test(self, test):
        self.assert_test_is_unique_in_suite(test)
        self._tests.append(test)
        self._selected_test_names.append(test.name)
    
    def add_sub_testsuite(self, sub_suite):
        self.assert_sub_suite_is_unique_in_suite(sub_suite)
        self._sub_testsuites.append(sub_suite)
    
    def load_generated_tests(self):
        pass
    
    def get_test(self, test_name):
        for test in self._tests:
            if test.name == test_name:
                return test
        raise ProgrammingError("unknown test '%s'" % test_name)
    
    def get_tests(self, filtered=True):
        if filtered:
            return list(filter(lambda t: self.is_test_selected(t), self._tests))
        else:
            return self._tests
    
    def get_sub_testsuites(self, filtered=True):
        if filtered:
            return list(filter(lambda s: s.has_selected_tests(deep=True), self._sub_testsuites))
        else:
            return self._sub_testsuites
    
    def get_suite_name(self):
        return self.name
    
    def get_suite_description(self):
        return self.description
    
    def get_fixtures(self, filtered=True, recursive=True):
        fixtures = []
        for test in self.get_tests(filtered):
            fixtures.extend(test.get_params())
        if recursive:
            for sub_suite in self.get_sub_testsuites(filtered):
                fixtures.extend(sub_suite.get_fixtures())
        
        return get_distincts_in_list(fixtures)
        
    ###
    # Compute tests metadata with metadata inherited from parent suite
    ###
    
    def get_inherited_test_paths(self, test):
        return list(map(lambda s: s.get_path_str(), self.get_path())) + [self.get_test_path_str(test)]

    def get_inherited_test_descriptions(self, test):
        return list(map(lambda s: s.description, self.get_path())) + [test.description]
    
    def get_inherited_test_tags(self, test):
        tags = []
        for suite in self.get_path():
            tags.extend(suite.tags)
        tags.extend(test.tags)
        return get_distincts_in_list(tags)
    
    def get_inherited_test_properties(self, test):
        properties = {}
        for suite in self.get_path():
            properties.update(suite.properties)
        properties.update(test.properties)
        return properties
    
    def get_inherited_test_links(self, test):
        links = []
        for suite in self.get_path():
            links.extend(suite.links)
        links.extend(test.links)
        return get_distincts_in_list(links)
    
    ###
    # Filtering methods
    ###
    
    def apply_filter(self, filter):
        self._selected_test_names = [ ]
        
        for test in self._tests:
            if filter.match_test(test, self):
                self._selected_test_names.append(test.name)
        
        for suite in self._sub_testsuites:
            suite.apply_filter(filter)

    def has_selected_tests(self, deep=True):
        if deep:
            if self._selected_test_names:
                return True
             
            for suite in self._sub_testsuites:
                if suite.has_selected_tests():
                    return True
             
            return False
        else:
            return bool(self._selected_test_names)
    
    def is_test_selected(self, test):
        return test.name in self._selected_test_names

def add_test_in_testsuite(test, suite, before_test=None, after_test=None):
    # pre-checks
    if before_test and after_test:
        raise ProgrammingError("before_test and after_test are mutually exclusive")
    
    if hasattr(suite, test.name):
        raise ProgrammingError("Object %s has already an attribute named '%s'" % (suite, test.name))
    
    # build test func metadata
    md = test.callback._lccmetadata = Metadata()
    md.is_test = True
    md.name = test.name
    md.description = test.description
    md.tags.extend(test.tags)
    md.properties.update(test.properties)
    md.links.extend(test.links)
    
    # set test func rank
    if before_test or after_test:
        ref_test_name = before_test if before_test else after_test
        test_methods = get_test_methods_from_class(suite)
        try:
            ref_test_obj = next(t for t in test_methods if t._lccmetadata.name == ref_test_name)
        except StopIteration:
            raise ProgrammingError("There is no base test named '%s' in class %s" % (ref_test_name, suite))
        
        if before_test:
            md.rank = ref_test_obj._lccmetadata.rank
            for test_method in filter(lambda t: t._lccmetadata.rank >= md.rank , test_methods):
                test_method._lccmetadata.rank += 1
        else: # after_test
            md.rank = ref_test_obj._lccmetadata.rank
            for test_method in filter(lambda t: t._lccmetadata.rank <= md.rank , test_methods):
                test_method._lccmetadata.rank -= 1
    else:
        md.rank = get_metadata_next_rank()
    
    # set test func and suite test method 
    setattr(suite, test.name, test.callback.__get__(suite))

def add_tests_in_testsuite(tests, suite, before_test=None, after_test=None):
    if before_test and after_test:
        raise ProgrammingError("before_test and after_test are mutually exclusive")
     
    if after_test:
        previous_test = after_test
        for test in tests:
            add_test_in_testsuite(test, suite, after_test=previous_test)
            previous_test = test.name
    else:
        for test in tests:
            add_test_in_testsuite(test, suite, before_test=before_test)

def is_testsuite(obj):
    return inspect.isclass(obj) and \
        hasattr(obj, "_lccmetadata") and \
        obj._lccmetadata.is_testsuite

def is_test(obj):
    return inspect.ismethod(obj) and \
        hasattr(obj, "_lccmetadata") and \
        obj._lccmetadata.is_test

def load_test_from_method(method):
    md = method._lccmetadata
    test = Test(md.name, md.description, method)
    test.tags.extend(md.tags)
    test.properties.update(md.properties)
    test.links.extend(md.links)
    return test

def get_test_methods_from_class(obj):
    return sorted(filter(is_test, map(lambda n: getattr(obj, n), dir(obj))), key=lambda m: m._lccmetadata.rank)

def get_sub_suites_from_class(obj):
    return sorted(filter(is_testsuite, map(lambda n: getattr(obj, n), dir(obj))), key=lambda c: c._lccmetadata.rank)

def load_testsuite_from_class(klass, parent_suite=None):
    md = klass._lccmetadata
    inst = klass()
    suite = TestSuite(md.name, md.description)
    suite.tags.extend(md.tags)
    suite.properties.update(md.properties)
    suite.links.extend(md.links)
    
    for hook_name in "setup_test", "teardown_test", "setup_suite", "teardown_suite":
        if hasattr(suite, hook_name):
            suite.add_hook(hook_name, getattr(suite, hook_name))

    for test_method in get_test_methods_from_class(inst):
        suite.add_test(load_test_from_method(test_method))
    
    for sub_suite_klass in get_sub_suites_from_class(inst):
        suite.add_sub_testsuite(load_testsuite_from_class(sub_suite_klass, parent_suite=suite))

    return suite