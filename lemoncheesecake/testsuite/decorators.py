'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect

from lemoncheesecake.testsuite.core import Test, TestSuite
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "test", "tags", "prop", "suite_rank", "link"

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
        if "tags" in obj.__dict__:
            obj.tags.extend(tag_names)
        elif hasattr(obj, "tags"):
            obj.tags = obj.tags + list(tag_names)
        else:
            obj.tags = list(tag_names)
        return obj
    return wrapper

def prop(key, value):
    """Decorator, add a property (key/value) to a test or a testsuite"""
    def wrapper(obj):
        assert_test_or_testsuite(obj)
        if "properties" in obj.__dict__:
            obj.properties[key] = value
        elif hasattr(obj, "properties"):
            props = obj.properties.copy()
            props[key]= value
            obj.properties = props
        else:
            obj.properties = { key: value }
        return obj
    return wrapper

def suite_rank(value):
    """Decorator, set the suite rank of a suite inside its parent suite"""
    def wrapper(klass):
        klass._rank = value
        return klass
    return wrapper

def link(url, name=None):
    """Decorator, set an LINK (with an optional friendly name) to a test or a testsuite"""
    def wrapper(obj):
        assert_test_or_testsuite(obj)
        if "links" in obj.__dict__:
            obj.links.append((url, name))
        elif hasattr(obj, "links"):
            obj.links = obj.links + [(url, name)]
        else:
            obj.links = [(url, name)]
        return obj
    return wrapper
