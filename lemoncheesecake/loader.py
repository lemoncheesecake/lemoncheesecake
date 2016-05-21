'''
Created on May 15, 2016

@author: nicolas
'''

import sys
import os.path
import re
import glob
import importlib

def suite_rank(value):
    def wrapper(klass):
        klass._rank = value
        return klass
    return wrapper

def _strip_py_ext(filename):
    return re.sub("\.py$", "", filename)

def _load_testsuite(filename):
    mod_path = _strip_py_ext(filename.replace("/", "."))
    mod_name = mod_path.split(".")[-1]

    loaded_mod = importlib.import_module(mod_path)
    try:
        klass = getattr(loaded_mod, mod_name)
    except AttributeError:
        raise Exception("Cannot find class '%s' in '%s'" % (mod_name, loaded_mod.__file__))
    return klass

def load_testsuites_from_directory(dir, recursive=True):
    suites = [ ]
    for filename in glob.glob(os.path.join(dir, "*.py")):
        if os.path.basename(filename).startswith("__"):
            continue
        suite = _load_testsuite(filename)
        if recursive:
            suite_subdir = _strip_py_ext(filename) + "_suites"
            if os.path.isdir(suite_subdir):
                sub_suites = load_testsuites_from_directory(suite_subdir, recursive=True)
                suite.sub_testsuite_classes = suite.sub_testsuite_classes + sub_suites
        suites.append(suite)
    if len(list(filter(lambda s: hasattr(s, "_rank"), suites))) == len(suites):
        suites.sort(key=lambda s: s._rank)
    return suites