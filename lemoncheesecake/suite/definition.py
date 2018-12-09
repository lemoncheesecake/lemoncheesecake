'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect
import copy

from lemoncheesecake.suite.core import InjectedFixture
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "add_test_into_suite", "add_test_in_suite", "add_tests_in_suite", "get_metadata", \
    "suite", "test", "tags", "prop", "link", "disabled", "conditional", "hidden", "depends_on", "inject_fixture"


class Metadata(object):
    _next_rank = 1

    def __init__(self):
        self.is_test = False
        self.is_suite = False
        self.name = None
        self.description = None
        self.properties = {}
        self.tags = []
        self.links = []
        self.rank = 0
        self.dependencies = []
        self.disabled = False
        self.condition = None


def get_metadata_next_rank():
    rank = Metadata._next_rank
    Metadata._next_rank += 1
    return rank


def add_test_into_suite(test, suite):
    if not hasattr(suite, "_lccgeneratedtests"):
        suite._lccgeneratedtests = []
    suite._lccgeneratedtests.append(test)


def add_test_in_suite(test, suite, before_test=None, after_test=None):
    """
    backward-compatibility function: use add_test_into_suite instead
    before_test and after_test arguments are simply ignored
    """
    if not test.rank:
        test.rank = get_metadata_next_rank()
    add_test_into_suite(test, suite)


def add_tests_in_suite(tests, suite, before_test=None, after_test=None):
    """
    backward-compatibility function: loop over tests and use add_test_into_suite instead
    before_test and after_test arguments are simply ignored
    """
    for test in tests:
        add_test_into_suite(test, suite)


_objects_with_metadata = []
def get_metadata(obj):
    global _objects_with_metadata

    if hasattr(obj, "_lccmetadata"):
        if obj not in _objects_with_metadata:  # metadata comes from the superclass
            obj._lccmetadata = copy.deepcopy(obj._lccmetadata)
        return obj._lccmetadata
    else:
        obj._lccmetadata = Metadata()
        _objects_with_metadata.append(obj)
        return obj._lccmetadata


def suite(description, name=None, rank=None):
    """Decorator, mark a class as a suite class"""
    def wrapper(klass):
        if not inspect.isclass(klass):
            raise ProgrammingError("%s is not a class (suite decorator can only be used on a class)" % klass)
        md = get_metadata(klass)
        if md.dependencies:
            raise ProgrammingError("'depends_on' can not be used on a suite class")
        md.is_suite = True
        md.rank = rank if rank is not None else get_metadata_next_rank()
        md.name = name or klass.__name__
        md.description = description
        return klass
    return wrapper


def test(description, name=None):
    """Decorator, make a method as a test method"""
    def wrapper(func):
        if not inspect.isfunction(func):
            raise ProgrammingError("%s is not a function (test decorator can only be used on a function)" % func)
        md = get_metadata(func)
        md.is_test = True
        md.rank = get_metadata_next_rank()
        md.name = name or func.__name__
        md.description = description
        return func
    return wrapper


def tags(*tag_names):
    """Decorator, add tags to a test or a suite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.tags.extend(tag_names)
        return obj
    return wrapper


def prop(key, value):
    """Decorator, add a property (key/value) to a test or a suite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.properties[key] = value
        return obj
    return wrapper


def link(url, name=None):
    """Decorator, set a link (with an optional friendly name) to a test or a suite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.links.append((url, name))
        return obj
    return wrapper


def disabled():
    """Decorator, disable a test or a suite"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.disabled = True
        return obj
    return wrapper


def conditional(condition):
    """Decorator, the test or suite will only appear if the given condition callback return a true value"""
    def wrapper(obj):
        md = get_metadata(obj)
        md.condition = condition
        return obj
    return wrapper


def hidden():
    return conditional(lambda _: False)


def depends_on(*deps):
    """
    Decorator, only applicable to a test. Add dependencies to a test.

    :param deps: the list of test paths that the current is depending on.
    """
    def wrapper(obj):
        md = get_metadata(obj)
        if md.is_suite:
            raise ProgrammingError("'depends_on' can not be used on a suite class")
        md.dependencies.extend(deps)
        return obj
    return wrapper


def inject_fixture(fixture_name=None):
    return InjectedFixture(fixture_name)