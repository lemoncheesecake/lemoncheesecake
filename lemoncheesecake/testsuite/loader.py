'''
Created on Feb 5, 2017

@author: nicolas
'''

import os.path as osp
import inspect

from lemoncheesecake.importer import get_matching_files, get_py_files_from_dir, strip_py_ext, import_module
from lemoncheesecake.exceptions import UserError, ProgrammingError, ImportTestSuiteError, InvalidMetadataError, serialize_current_exception
from lemoncheesecake.testsuite.core import Test, TestSuite, TESTSUITE_HOOKS

__all__ = "load_testsuite_from_file", "load_testsuites_from_files", "load_testsuites_from_directory", \
    "load_testsuite_from_class", "load_testsuites_from_classes"

def is_testsuite_class(obj):
    return inspect.isclass(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_testsuite

def is_test_method(obj):
    return inspect.ismethod(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test

def is_test_function(obj):
    return inspect.isfunction(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test

def load_test(obj):
    md = obj._lccmetadata
    test = Test(md.name, md.description, obj)
    test.tags.extend(md.tags)
    test.properties.update(md.properties)
    test.links.extend(md.links)
    return test

def load_test_from_method(method):
    return load_test(method)

def load_test_from_function(func):
    return load_test(func)

def _list_object_attributes(obj):
    return [getattr(obj, n) for n in dir(obj) if not n.startswith("__")]

def get_test_methods_from_class(obj):
    return sorted(filter(is_test_method, _list_object_attributes(obj)), key=lambda m: m._lccmetadata.rank)

def get_sub_suites_from_class(obj):
    return sorted(filter(is_testsuite_class, _list_object_attributes(obj)), key=lambda c: c._lccmetadata.rank)

def get_test_functions_from_module(mod):
    return filter(is_test_function, _list_object_attributes(mod))

def get_suite_classes_from_module(mod):
    return filter(is_testsuite_class, _list_object_attributes(mod))

def load_testsuite_from_class(klass):
    md = klass._lccmetadata
    try:
        inst = klass()
    except UserError as e:
        raise e # propagate UserError
    except Exception:
        raise ProgrammingError("Got an unexpected error while instanciating testsuite class '%s':%s" % (
            klass.__name__, serialize_current_exception()
        ))
    suite = TestSuite(inst, md.name, md.description)
    suite.tags.extend(md.tags)
    suite.properties.update(md.properties)
    suite.links.extend(md.links)
    suite.rank = md.rank
    
    for hook_name in TESTSUITE_HOOKS:
        if hasattr(inst, hook_name):
            suite.add_hook(hook_name, getattr(inst, hook_name))

    for test_method in get_test_methods_from_class(inst):
        suite.add_test(load_test_from_method(test_method))
    
    for sub_suite_klass in get_sub_suites_from_class(inst):
        suite.add_sub_testsuite(load_testsuite_from_class(sub_suite_klass))

    return suite

def load_testsuites_from_classes(klasses):
    return [load_testsuite_from_class(klass) for klass in klasses]

def load_testsuite_from_module(mod):
    # TODO: find a better way to workaround circular import 
    from lemoncheesecake.testsuite.definition import get_metadata_next_rank
    
    suite_info = getattr(mod, "TESTSUITE")
    suite_name = inspect.getmodulename(inspect.getfile(mod))
    
    try:
        suite_description = suite_info["description"]
    except KeyError:
        raise InvalidMetadataError("Missing description in '%s' testsuite information" % mod.__file__)
    
    suite = TestSuite(None, suite_name, suite_description)
    suite.tags.extend(suite_info.get("tags", []))
    suite.properties.update(suite_info.get("properties", []))
    suite.links.extend(suite_info.get("links", []))
    suite.rank = suite_info.get("rank", get_metadata_next_rank())

    for hook_name in TESTSUITE_HOOKS:
        if hasattr(mod, hook_name):
            suite.add_hook(hook_name, getattr(mod, hook_name))

    for func in get_test_functions_from_module(mod):
        suite.add_test(load_test_from_function(func))

    sub_suites = []
    for klass in get_suite_classes_from_module(mod):
        sub_suites.append(load_testsuite_from_class(klass))
    sub_suites.sort(key=lambda suite: suite.rank)
    for sub_suite in sub_suites:
        suite.add_sub_testsuite(sub_suite)

    return suite

def load_testsuite_from_file(filename):
    """Get testsuite from Python module.
    
    A valid module is either:
    - a module containing a dict name 'TESTSUITE' with keys:
      - description (mandatory)
      - tags (optional)
      - properties (optional)
      - links (optional)
      - rank (optional)
    - a module that contains a testsuite class with the same name as the module name
    
    Raise a ImportTestSuiteError if the testsuite class cannot be imported.
    """
    try:
        mod = import_module(filename)
    except ImportError:
        raise ImportTestSuiteError(
            "Cannot import file '%s': %s" % (filename, serialize_current_exception(show_stacktrace=True))
        )
    
    if hasattr(mod, "TESTSUITE"):
        suite = load_testsuite_from_module(mod)
    else:
        mod_name = strip_py_ext(osp.basename(filename))
        try:
            klass = getattr(mod, mod_name)
        except AttributeError:
            raise ImportTestSuiteError("Cannot find class '%s' in '%s'" % (mod_name, mod.__file__))
        suite = load_testsuite_from_class(klass)
    return suite

def load_testsuites_from_files(patterns, excluding=[]):
    """
    Import testsuites from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: load_testsuites_from_files("test_*.py")
    """
    return [load_testsuite_from_file(f) for f in get_matching_files(patterns, excluding)]

def load_testsuites_from_directory(dir, recursive=True):
    """Find testsuite classes in modules found in dir.
    
    The function expect that:
    - each module (.py file) contains a class that inherits TestSuite
    - the class name must have the same name as the module name (if the module is foo.py 
      the class must be named foo)
    If the recursive argument is set to True, sub testsuites will be searched in a directory named
    from the suite module: if the suite module is "foo.py" then the sub suites directory must be "foo".
    
    Raise ImportTestSuiteError if one or more testsuite cannot be imported.
    """
    if not osp.exists(dir):
        raise ImportTestSuiteError("Directory '%s' does not exist" % dir)
    suites = [ ]
    for filename in get_py_files_from_dir(dir):
        suite = load_testsuite_from_file(filename)
        if recursive:
            subsuites_dir = strip_py_ext(filename)
            if osp.isdir(subsuites_dir):
                for sub_suite in load_testsuites_from_directory(subsuites_dir, recursive=True):
                    suite.add_sub_testsuite(sub_suite)
        suites.append(suite)
    suites.sort(key=lambda suite: suite.rank)
    return suites
