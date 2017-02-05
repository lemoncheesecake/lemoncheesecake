'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect
import copy

from lemoncheesecake.testsuite.core import Test, TestSuite, Metadata, get_metadata_next_rank
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "test", "testsuite", "tags", "prop", "link"

_objects_with_metadata = []
def get_metadata(obj):
    global _objects_with_metadata
    
    if hasattr(obj, "_lccmetadata"):
        if obj not in _objects_with_metadata: # metadata comes from the superclass
            obj._lccmetadata = copy.deepcopy(obj._lccmetadata)
        return obj._lccmetadata
    else:
        obj._lccmetadata = Metadata()
        _objects_with_metadata.append(obj)
        return obj._lccmetadata

def testsuite(description, rank=None):
    """Decorator, mark a class as a testsuite class"""
    def wrapper(klass):
        if not inspect.isclass(klass):
            raise ProgrammingError("%s is not a class (testsuite decorator can only be used on a class)" % klass)
        md = get_metadata(klass)
        md.is_testsuite = True
        if rank != None:
            md.rank = get_metadata_next_rank()
        md.name = klass.__name__
        md.description = description
        return klass
    return wrapper

def test(description):
    """Decorator, make a method as a test method"""
    def wrapper(func):
        if not inspect.isfunction(func):
            raise ProgrammingError("%s is not a function (test decorator can only be used on a function)" % func)
        md = get_metadata(func)
        md.is_test = True
        md.rank = get_metadata_next_rank()
        md.name = func.__name__
        md.description = description
        return func
    return wrapper

def tags(*tag_names):
    """Decorator, add tags to a test or a testsuite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.tags.extend(tag_names)
        return obj
    return wrapper

def prop(key, value):
    """Decorator, add a property (key/value) to a test or a testsuite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.properties[key] = value
        return obj
    return wrapper

def link(url, name=None):
    """Decorator, set a link (with an optional friendly name) to a test or a testsuite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.links.append((url, name))
        return obj
    return wrapper
