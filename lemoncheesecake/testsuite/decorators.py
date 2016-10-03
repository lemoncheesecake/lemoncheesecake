'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.testsuite.core import Test, TestSuite
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "test", "tags", "prop", "suite_rank", "url"

class StaticTestDecorator:
    def __init__(self, description):
        self.description = description
    
    def __call__(self, callback):
        callback = callback
        id = callback.__name__
        
        return Test(id, self.description, callback)

def assert_test_or_testsuite(obj):
    if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
        raise ProgrammingError("Tags can only be added to Test and TestSuite objects (got %s)" % type(obj))

def test(description):
    """Decorator, make a test from a TestSuite method"""
    return StaticTestDecorator(description)

def tags(*tag_names):
    """Decorator, add tags to a test or a testsuite"""
    def wrapper(obj):
        assert_test_or_testsuite(obj)
        obj.tags = tag_names
        return obj
    return wrapper

def prop(key, value):
    """Decorator, add a property (key/value) to a test or a testsuite"""
    def wrapper(obj):
        assert_test_or_testsuite(obj)
        obj.properties[key] = value
        return obj
    return wrapper

def suite_rank(value):
    """Decorator, set the suite rank of a suite inside its parent suite"""
    def wrapper(klass):
        klass._rank = value
        return klass
    return wrapper

def url(url, name=None):
    """Decorator, set an URL (with an optional friendly name) to a test or a testsuite"""
    def wrapper(obj):
        assert_test_or_testsuite(obj)
        obj.urls.append((url, name))
        return obj
    return wrapper