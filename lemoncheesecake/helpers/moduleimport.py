import os
import os.path as osp
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
    mod_name = strip_py_ext(osp.basename(path))
    try:
        spec = importlib.util.spec_from_file_location(mod_name, path)
        module = importlib.util.module_from_spec(spec)
        # NB: we should not make the module visible in sys.modules because a module without package could
        # conflict with another module (suite or Python module) of the same name.
        # Unfortunately, this behavior must be kept for backward compatibility with the use-case where
        # a test is programmatically added to a module: add_test_into_suite(..., sys.modules[__name__])
        # The best idea would be to:
        # - create a dedicated function to handle this use-case
        # - deprecate the usage of sys.modules within suite modules
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    except Exception:
        raise ModuleImportError(
            "Error while importing file '%s': %s" % (path, serialize_current_exception(show_stacktrace=True))
        )

    return module
