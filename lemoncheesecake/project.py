'''
Created on Dec 10, 2016

@author: nicolas
'''

import os
import sys
import shutil
import imp
import inspect

from lemoncheesecake.testsuite import TestSuite
from lemoncheesecake.fixtures import Fixture
from lemoncheesecake.worker import Worker
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.reporting import reportdir, backends
from lemoncheesecake import reporting
from lemoncheesecake import loader
from lemoncheesecake.exceptions import ProjectError
from lemoncheesecake.utils import get_resource_path

DEFAULT_REPORTING_BACKENDS = reporting.get_available_backends()

PROJECT_SETTINGS_FILE = "project.py"

def find_project_file():
    return os.environ.get("LCC_PROJECT_FILE", os.path.join(os.getcwd(), PROJECT_SETTINGS_FILE))

def _check_class(klass):
    def wrapper(name, value):
        if not inspect.isclass(value) or not issubclass(value, klass):
            return "'%s' has an incorrect value, '%s' is not a subclass of %s" % (name, value, klass)
        return None
    return wrapper

def _check_class_instance(klass):
    def wrapper(name, value):
        if not isinstance(value, klass):
            return "'%s' has an incorrect value, %s is not an instance of %s" % (name, value, klass)
        return None
    return wrapper

def _check_type(type_):
    def wrapper(name, value):
        if type(value) is not type_:
            return "'%s' has an incorrect value, '%s' is not a '%s'" % (name, value, type_)
        return None
    return wrapper

def _check_func(args_nb=None):
    def wrapper(name, value):
        if not callable(value):
            return "'%s' has an incorrect value, '%s' is not a function" % (name, value)
        argspec = inspect.getargspec(value)
        if args_nb != None and len(argspec.args) != args_nb:
            return "'%s' function takes %s arguments instead of %d" % (len(argspec.args), args_nb)
        return None
    return wrapper

def _check_report_backend(name, value):
    if not isinstance(value, reporting.ReportingBackend):
        return "%s does not inherit lemoncheesecake.reporting.ReportingBackend" % value
    return None

class Project:
    def __init__(self, project_file=None):
        self._project_file = project_file or find_project_file()
        self._project_dir = os.path.dirname(self._project_file)
        self._cache = {}
        
        sys.path.insert(0, self._project_dir)
        try:
            self._settings = imp.load_source("__project", self._project_file)
        except Exception as e:
            raise ProjectError(self._project_file, e)
        finally:
            try:
                del sys.modules["__project"]
            except KeyError:
                pass
            sys.path.pop(0)
    
    def get_project_dir(self):
        return self._project_dir
        
    def _get_param(self, name, checker, is_list=False, is_dict=False, required=True, default=None, cache_value=True):
        if name in self._cache:
            return self._cache[name]
        
        if not hasattr(self._settings, name):
            if required:
                raise ProjectError(self._project_file, "mandatory parameter '%s' is missing" % name)
            else:
                if cache_value:
                    self._cache[name] = default
                return default
            
        value = getattr(self._settings, name)

        if is_list:
            if type(value) not in (list, tuple):
                raise ProjectError(self._project_file, "parameter '%s' must be a list or a tuple" % name)
            for v in value:
                error = checker(name, v)
                if error:
                    raise ProjectError(self._project_file, error)
        elif is_dict:
            if type(value) != dict:
                raise ProjectError(self._project_file, "parameter '%s' must be a dict" % name)
            for v in value.values():
                error = checker(name, v)
                if error:
                    raise ProjectError(self._project_file, error)
        
        else:
            error = checker(name, value)
            if error:
                raise ProjectError(self._project_file, error)
    
        if cache_value:
            self._cache[name] = value
        return value
    
    def get_cli_extra_args_callback(self):
        return self._get_param("CLI_EXTRA_ARGS", _check_func(args_nb=1), required=False)
    
    def add_cli_extra_args(self, cli_args_parser):
        callback = self.get_cli_extra_args_callback()
        if callback:
            callback(cli_args_parser)
    
    def get_report_dir_creation_callback(self):
        return self._get_param("REPORT_DIR_CREATION", 
            _check_func(args_nb=1), required=False, 
            default=lambda top_dir: reportdir.report_dir_with_archiving(top_dir, reportdir.archive_dirname_datetime)
        )
    
    def get_testsuites_classes(self):
        return self._get_param("TESTSUITES", _check_class(TestSuite), is_list=True)

    def get_fixtures(self):
        return self._get_param("FIXTURES", _check_func(), is_list=True, required=False, default=[])
    
    def get_workers(self):
        return self._get_param("WORKERS", _check_class_instance(Worker), is_dict=True, required=False, default={})

    def _get_reporting_backends(self):
        if "REPORTING_BACKENDS" in self._cache:
            return self._cache["REPORTING_BACKENDS"]
        
        backends = self._get_param("REPORTING_BACKENDS", 
            _check_class_instance(reporting.ReportingBackend), is_list=True, required=False, default=DEFAULT_REPORTING_BACKENDS,
            cache_value=False
        )
        
        self._cache["REPORTING_BACKENDS"] = backends
        return backends

    def get_reporting_backends(self, capabilities=0, active_only=False):
        if active_only:
            backends = filter(lambda b: b.name in self.get_active_reporting_backend_names(), self._get_reporting_backends())
        else:
            backends = self._get_reporting_backends()
        return list(filter(
            lambda b: b.get_capabilities() & capabilities == capabilities, backends
        ))
    
    def get_active_reporting_backend_names(self):
        if "REPORTING_BACKENDS_ACTIVE" in self._cache:
            return self._cache["REPORTING_BACKENDS_ACTIVE"]
        
        existing_backends = {backend.name: backend.is_available() for backend in self._get_reporting_backends()}
        active = self._get_param("REPORTING_BACKENDS_ACTIVE", 
            _check_type(str), is_list=True, required=False, default=existing_backends,
            cache_value=False
        )
        for active_backend in active:
            if active_backend in existing_backends:
                if not existing_backends[active_backend]:
                    raise ProjectError(
                        self._project_file,
                        "In parameter REPORTING_BACKENDS_ACTIVE, backend '%s' is not available (available backends are: %s)" % (
                            active_backend, ", ".join([backend for backend, available in existing_backends.items() if available])
                    ))
            else:
                raise ProjectError(
                    self._project_file,
                    "In parameter REPORTING_BACKENDS_ACTIVE, backend '%s' does not exist (backends are: %s)" % (
                        active_backend, ", ".join(existing_backends.keys())
                ))
        
        self._cache["REPORTING_BACKENDS_ACTIVE"] = active
        return active

    def is_reporting_backend_active(self, backend_name):
        return backend_name in self.get_active_reporting_backend_names()
    
    def get_metadata_policy(self):
        return self._get_param("METADATA_POLICY", _check_class_instance(MetadataPolicy), required=False, default=MetadataPolicy())
    
    def get_before_test_run_hook(self):
        return self._get_param("RUN_HOOK_BEFORE_TESTS", _check_func(args_nb=1), required=False)

    def get_after_test_run_hook(self):
        return self._get_param("RUN_HOOK_AFTER_TESTS", _check_func(args_nb=1), required=False)
    
    def load_testsuites(self):
        return loader.load_testsuites(self.get_testsuites_classes(), self.get_metadata_policy())

def create_project(project_dir):
    p = os.path
    shutil.copyfile(get_resource_path(p.join("project", "template.py")), p.join(project_dir, PROJECT_SETTINGS_FILE))
    os.mkdir(p.join(project_dir, "tests"))
    os.mkdir(p.join(project_dir, "fixtures"))

def load_project(project_dir):
    return Project(os.path.join(project_dir, PROJECT_SETTINGS_FILE))
