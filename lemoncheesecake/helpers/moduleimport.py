import os
import sys
import glob
import fnmatch
import re
import importlib.util

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


def import_module(path):
    try:
        # NB: path is used as module name to avoid possible conflicting with Python modules using
        # the same name
        spec = importlib.util.spec_from_file_location(path, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path] = module
        spec.loader.exec_module(module)
    except Exception:
        raise ModuleImportError(
            "Error while importing file '%s': %s" % (path, serialize_current_exception(show_stacktrace=True))
        )

    return module
