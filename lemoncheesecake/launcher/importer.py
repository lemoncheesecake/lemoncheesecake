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

from lemoncheesecake.exceptions import ImportTestSuiteError

__all__ = "import_testsuite_from_file", "import_testsuites_from_directory"

def _strip_py_ext(filename):
    return re.sub("\.py$", "", filename)

def import_testsuite_from_file(filename):
    """Get testsuite class from Python module.
    
    The testsuite class must have the same name as the containing Python module.
    Raise a ImportTestSuiteError if the testsuite class cannot be imported.
    """
    mod_dir = os.path.dirname(filename)
    mod_name = _strip_py_ext(os.path.basename(filename))

    sys.path.insert(0, mod_dir)
    try:
        loaded_mod = importlib.import_module(mod_name)
    except ImportError as e:
        raise ImportTestSuiteError("Cannot import module %s: %s" % (mod_name, str(e)))
    finally:
        del sys.path[0]
    
    try:
        klass = getattr(loaded_mod, mod_name)
    except AttributeError:
        raise ImportTestSuiteError("Cannot find class '%s' in '%s'" % (mod_name, loaded_mod.__file__))
    return klass

def import_testsuites_from_files(patterns, excludes=[]):
    if type(patterns) not in (list, tuple):
        patterns = [patterns]
    if type(excludes) not in (list, tuple):
        excludes = [excludes]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    if excludes:
        tmp = files[:] # iterate on copy to be able to alter files
        for file in tmp:
            for exclude in excludes:
                if fnmatch.fnmatch(file, exclude):
                    files.remove(file)
                    break
    return [import_testsuite_from_file(f) for f in files]

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
    for filename in glob.glob(os.path.join(dir, "*.py")):
        if os.path.basename(filename).startswith("__"):
            continue
        suite = import_testsuite_from_file(filename)
        if recursive:
            subsuites_dir = _strip_py_ext(filename)
            if os.path.isdir(subsuites_dir):
                suite.sub_suites = import_testsuites_from_directory(subsuites_dir, recursive=True)
        suites.append(suite)
    if len(list(filter(lambda s: hasattr(s, "_rank"), suites))) == len(suites):
        suites.sort(key=lambda s: s._rank)
    return suites