'''
Created on Sep 10, 2016

@author: nicolas
'''

import os
import sys
import glob
import fnmatch
import re
import importlib

from lemoncheesecake.exceptions import ImportTestSuiteError, InvalidMetadataError

__all__ = "import_testsuite_from_file", "import_testsuites_from_directory"

def _strip_py_ext(filename):
    return re.sub("\.py$", "", filename)

def _get_py_files_from_dir(dir):
    return list(filter(
        lambda f: not os.path.basename(f).startswith("__"), glob.glob(os.path.join(dir, "*.py"))
    ))

def _get_matching_files(patterns, excluding=[]):
    if type(patterns) not in (list, tuple):
        patterns = [patterns]
    if type(excluding) not in (list, tuple):
        excluding = [excluding]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    if excluding:
        tmp = files[:] # iterate on copy to be able to alter files
        for file in tmp:
            for excluded in excluding:
                if fnmatch.fnmatch(file, excluded):
                    files.remove(file)
                    break
    return files

def _import_module(filename):
    mod_dir = os.path.dirname(filename)
    mod_name = _strip_py_ext(os.path.basename(filename))

    sys.path.insert(0, mod_dir)
    try:
        # FIXME: possibly mess-up a module with the same name
        try:
            del sys.modules[mod_name]
        except KeyError:
            pass
        mod = importlib.import_module(mod_name)
    except ImportError as e:
        raise ImportTestSuiteError("Cannot import module %s: %s" % (mod_name, str(e)))
    finally:
        del sys.path[0]
    
    return mod

def import_testsuite_from_file(filename):
    """Get testsuite class from Python module.
    
    The testsuite class must have the same name as the containing Python module.
    
    Raise a ImportTestSuiteError if the testsuite class cannot be imported.
    """
    mod = _import_module(filename)
    mod_name = _strip_py_ext(os.path.basename(filename))
    try:
        klass = getattr(mod, mod_name)
    except AttributeError:
        raise ImportTestSuiteError("Cannot find class '%s' in '%s'" % (mod_name, mod.__file__))
    return klass

def import_testsuites_from_files(patterns, excluding=[]):
    """
    Import testsuites from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: import_testsuites_from_files("test_*.py")
    """
    return [import_testsuite_from_file(f) for f in _get_matching_files(patterns, excluding)]

def import_testsuites_from_directory(dir, recursive=True):
    """Find testsuite classes in modules found in dir.
    
    The function expect that:
    - each module (.py file) contains a class that inherits TestSuite
    - the class name must have the same name as the module name (if the module is foo.py 
      the class must be named foo)
    If the recursive argument is set to True, sub testsuites will be searched in a directory named
    from the suite module: if the suite module is "foo.py" then the sub suites directory must be "foo".
    
    Raise ImportTestSuiteError if one or more testsuite cannot be imported.
    """
    suites = [ ]
    for filename in _get_py_files_from_dir(dir):
        suite = import_testsuite_from_file(filename)
        if recursive:
            subsuites_dir = _strip_py_ext(filename)
            if os.path.isdir(subsuites_dir):
                suite.sub_suites = import_testsuites_from_directory(subsuites_dir, recursive=True)
        suites.append(suite)
    if len(list(filter(lambda s: hasattr(s, "_rank"), suites))) == len(suites):
        suites.sort(key=lambda s: s._rank)
    return suites

def _load_testsuite(suite, loaded_tests, loaded_suites, metadata_policy):
        # process suite
        if suite.id in loaded_suites:
            raise InvalidMetadataError("A test suite with id '%s' has been registered more than one time" % suite.id)
        if metadata_policy:
            metadata_policy.check_suite_compliance(suite)
        loaded_suites[suite.id] = suite

        # process tests
        for test in suite.get_tests():
            if test.id in loaded_tests:
                raise InvalidMetadataError("A test with id '%s' has been registered more than one time" % test.id)
            if metadata_policy:
                metadata_policy.check_test_compliance(test)
            loaded_tests[test.id] = test
        
        # process sub suites
        for sub_suite in suite.get_sub_testsuites():
            _load_testsuite(sub_suite, loaded_tests, loaded_suites, metadata_policy)

def load_testsuites(suite_classes, metadata_policy=None):
    """Load testsuites classes.
    
    - testsuite classes get instantiated into objects
    - sanity checks are performed (among which unicity constraints)
    - test and testsuites are checked using metadata_policy
    """
    loaded_tests = {}
    loaded_suites = {}
    suites = []
    for suite_class in suite_classes:
        suite = suite_class()
        suite.load()
        suites.append(suite)
        _load_testsuite(suite, loaded_tests, loaded_suites, metadata_policy)
    return suites

def import_fixtures_from_file(filename):
    mod = _import_module(filename)
    funcs = []
    for sym_name in dir(mod):
        sym = getattr(mod, sym_name)
        if hasattr(sym, "_lccfixtureinfo"):
            funcs.append(sym)
    return funcs

def import_fixtures_from_files(patterns, excluding=[]):
    """
    Import fixtures from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: import_testsuites_from_files("test_*.py")
    """
    fixtures = []
    for file in _get_matching_files(patterns, excluding):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures

def import_fixtures_from_directory(dir):
    fixtures = []
    for file in _get_py_files_from_dir(dir):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures
