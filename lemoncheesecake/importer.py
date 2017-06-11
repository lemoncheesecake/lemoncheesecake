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
import warnings

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
        with warnings.catch_warnings():
            # would raise a warning since module's directory does not need to have a __init__.py
            warnings.simplefilter("ignore", ImportWarning)
            fh, path, description = imp.find_module(mod_name)
        try:
            mod = imp.load_module(package + mod_name, fh, path, description)
        finally:
            fh.close()
    finally:
        del sys.path[0]

    return mod
