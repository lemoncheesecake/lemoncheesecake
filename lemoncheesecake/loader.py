'''
Created on Sep 10, 2016

@author: nicolas
'''

import os
import sys
import glob
import fnmatch
import re
import imp

from lemoncheesecake.exceptions import ImportTestSuiteError

def strip_py_ext(filename):
    return re.sub("\.py$", "", filename)

def get_py_files_from_dir(dir):
    return list(filter(
        lambda f: not os.path.basename(f).startswith("__"), glob.glob(os.path.join(dir, "*.py"))
    ))

def get_matching_files(patterns, excluding=[]):
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

def import_module(filename):
    p = os.path
    mod_dir = p.dirname(filename)
    mod_name = strip_py_ext(p.basename(filename))

    sys.path.insert(0, mod_dir)
    try:
        package = "".join(p.splitdrive(mod_dir)[1].split(p.sep)[1:])
        fh, path, description = imp.find_module(mod_name)
        try:
            mod = imp.load_module(package + mod_name, fh, path, description)
        finally:
            fh.close()
    except ImportError as e:
        raise ImportTestSuiteError("Cannot import module %s: %s" % (mod_name, str(e)))
    finally:
        del sys.path[0]
    
    return mod

def import_fixtures_from_file(filename):
    mod = import_module(filename)
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
    for file in get_matching_files(patterns, excluding):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures

def import_fixtures_from_directory(dir):
    fixtures = []
    for file in get_py_files_from_dir(dir):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures
