'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import InvalidMetadataError, ProgrammingError, InternalError
from lemoncheesecake.utils import get_distincts_in_list

TESTSUITE_HOOKS = "setup_test", "teardown_test", "setup_suite", "teardown_suite"

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

def _assert_valid_hook_name(hook_name):
    if hook_name not in TESTSUITE_HOOKS:
        raise InternalError("Invalid hook name '%s'" % hook_name)

class TestSuite:
    def __init__(self, obj, name, description, parent_suite=None):
        self.obj = obj
        self.parent_suite = parent_suite
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
        _assert_valid_hook_name(hook_name)
        self._hooks[hook_name] = func
    
    def has_hook(self, hook_name):
        _assert_valid_hook_name(hook_name)
        return hook_name in self._hooks
    
    def get_hook(self, hook_name):
        _assert_valid_hook_name(hook_name)
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
        depth = 0
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
    
    def set_worker(self, worker_name, worker):
        if not self.obj:
            return
        if hasattr(self.obj, worker_name):
            raise ProgrammingError("Cannot set worker '%s' into testsuite '%s', it already has an attribute with that name" % (
                worker_name, self.obj
            ))
        setattr(self.obj, worker_name, worker)

def walk_testsuites(testsuites, testsuite_func=None, test_func=None):
    def do_walk(suite):
        if testsuite_func:
            testsuite_func(suite)
        if test_func:
            for test in suite.get_tests():
                test_func(test, suite)
        for sub_suite in suite.get_sub_testsuites():
            do_walk(sub_suite)
    for suite in testsuites:
        do_walk(suite)    

def walk_tests(testsuites, func):
    walk_testsuites(testsuites, test_func=func)

def filter_testsuites(suites, filtr):
    filtered = []
    for suite in suites:
        suite.apply_filter(filtr)
        if suite.has_selected_tests():
            filtered.append(suite)
    return filtered
