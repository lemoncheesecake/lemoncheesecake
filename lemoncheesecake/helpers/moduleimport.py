'''
Created on Sep 10, 2016

@author: nicolas
'''

import os
import os.path as osp
import sys
import glob
import fnmatch
import re
import imp
import warnings

from lemoncheesecake.exceptions import serialize_current_exception, ModuleImportError


def strip_py_ext(filename):
    return re.sub(r"\.py$", "", filename)


def get_py_files_from_dir(dir):
    return \
        sorted(
            filter(
                lambda f: not os.path.basename(f).startswith("__"), glob.glob(os.path.join(dir, "*.py"))
            )
        )


def get_matching_files(patterns, excluding=[]):
    if type(patterns) not in (list, tuple):
        patterns = [patterns]
    if type(excluding) not in (list, tuple):
        excluding = [excluding]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    if excluding:
        tmp = files[:]  # iterate on copy to be able to alter files
        for file in tmp:
            for excluded in excluding:
                if fnmatch.fnmatch(file, excluded):
                    files.remove(file)
                    break
    return sorted(files)


def import_module(mod_filename):
    mod_dir = osp.dirname(mod_filename)
    mod_name = strip_py_ext(osp.basename(mod_filename))

    ###
    # Find module
    ###
    sys.path.insert(0, mod_dir)
    try:
        with warnings.catch_warnings():
            # would raise a warning since module's directory does not need to have a __init__.py
            warnings.simplefilter("ignore", ImportWarning)
            fh, path, description = imp.find_module(mod_name)
    except ImportError:
        raise ModuleImportError(
            "Cannot find module '%s': %s" % (mod_filename, serialize_current_exception(show_stacktrace=True))
        )
    finally:
        del sys.path[0]

    ###
    # Load module
    ###
    package_name = "".join(osp.splitdrive(mod_dir)[1].split(osp.sep)[1:])
    try:
        mod = imp.load_module(package_name + mod_name, fh, path, description)
    except ImportError:
        raise ModuleImportError(
            "Cannot import file '%s': %s" % (mod_filename, serialize_current_exception(show_stacktrace=True))
        )
    except Exception:
        raise ModuleImportError(
            "Error while importing file '%s': %s" % (mod_filename, serialize_current_exception(show_stacktrace=True))
        )
    finally:
        fh.close()

    return mod
