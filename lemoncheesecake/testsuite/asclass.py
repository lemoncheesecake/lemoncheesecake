'''
Created on Feb 5, 2017

@author: nicolas
'''

import inspect

from lemoncheesecake.exceptions import ProgrammingError
from lemoncheesecake.testsuite.core import Test, TestSuite

__all__ = ("load_testsuite_from_class", "add_test_in_testsuite", "add_tests_in_testsuite")

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
        self.rank = 0

def get_metadata_next_rank():
    rank = Metadata._next_rank
    Metadata._next_rank += 1
    return rank

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

def _list_object_attributes(obj):
    return [getattr(obj, n) for n in dir(obj) if not n.startswith("__")]

def get_test_methods_from_class(obj):
    return sorted(filter(is_test, _list_object_attributes(obj)), key=lambda m: m._lccmetadata.rank)

def get_sub_suites_from_class(obj):
    sub_suites = obj.sub_suites[:] if hasattr(obj, "sub_suites") else []
    return sorted(filter(is_testsuite, _list_object_attributes(obj) + sub_suites), key=lambda c: c._lccmetadata.rank)

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