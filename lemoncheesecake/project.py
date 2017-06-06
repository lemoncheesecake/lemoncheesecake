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
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.reporting import ReportingBackend, get_available_backends
from lemoncheesecake.reporting.reportdir import report_dir_with_archiving, archive_dirname_datetime
from lemoncheesecake.exceptions import ProjectError, UserError, serialize_current_exception
from lemoncheesecake.utils import get_resource_path, get_callable_args
from lemoncheesecake.importer import import_module

DEFAULT_REPORTING_BACKENDS = get_available_backends()

PROJECT_SETTINGS_FILE = "project.py"

def _find_file_going_up(filename, dirname):
    if os.path.exists(os.path.join(dirname, filename)):
        return os.path.join(dirname, filename)
    
    parent_dirname = os.path.dirname(dirname)
    if parent_dirname == dirname:
        return None # root directory has been reached
    
    return _find_file_going_up(filename, parent_dirname)

def find_project_file():
    filename = os.environ.get("LCC_PROJECT_FILE")
    if filename != None:
        return filename if os.path.exists(filename) else None
    
    filename = _find_file_going_up(PROJECT_SETTINGS_FILE, os.getcwd())
    return filename # filename can be None

def _check_class(klass=None):
    def wrapper(name, value):
        if klass:
            if not inspect.isclass(value) or not issubclass(value, klass):
                return "'%s' has an incorrect value, %s is not a subclass of %s" % (name, repr(value), klass)
        else:
            if not inspect.isclass(value):
                return "'%s' has an incorrect value, %s is not a class" % (name, repr(value))
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
        if args_nb != None:
            args = get_callable_args(value)
            if len(args) != args_nb:
                return "'%s' function expect %s arguments, got %d" % (name, args_nb, len(args))
        return None
    return wrapper

def _check_report_backend(name, value):
    if not isinstance(value, ReportingBackend):
        return "%s does not inherit lemoncheesecake.reporting.ReportingBackend" % value
    return None

def _param_error(param_name, error_msg):
    raise ProjectError("Error with parameter '%s' of the project file: %s" % (param_name, error_msg))

class Project:
    def __init__(self, project_file):
        self._project_file = project_file
        self._project_dir = os.path.dirname(self._project_file)

        try:
            self._settings = import_module(self._project_file)
        except UserError as e:
            raise e # propagate UserError
        except Exception:
            raise ProjectError("Got an unexpected error while loading project:%s" % (
                serialize_current_exception()
            ))

        ###
        # Fetch parameters from project settings
        ###
        self._raw_params = {}
        def _(name, *args, **kwargs):
            self._raw_params[name] = self._get_param(name, *args, **kwargs)
        _("CLI_EXTRA_ARGS", _check_func(args_nb=1), required=False)
        _("REPORT_DIR_CREATION", 
            _check_func(args_nb=1), required=False, 
            default=lambda top_dir: report_dir_with_archiving(top_dir, archive_dirname_datetime)
        )
        _("TESTSUITES", _check_class_instance(TestSuite), is_list=True)
        _("FIXTURES", _check_class_instance(Fixture), is_list=True, required=False, default=[])
        _("REPORTING_BACKENDS", 
            _check_class_instance(ReportingBackend), is_list=True, required=False, default=DEFAULT_REPORTING_BACKENDS
        )
        _("REPORTING_BACKENDS_ACTIVE", 
            _check_type(str), is_list=True, required=False, default=None
        )
        _("METADATA_POLICY", _check_class_instance(MetadataPolicy), required=False, default=MetadataPolicy())
        _("RUN_HOOK_BEFORE_TESTS", _check_func(args_nb=1), required=False)
        _("RUN_HOOK_AFTER_TESTS", _check_func(args_nb=1), required=False)
        
        ###
        # Cross checks between parameters
        ###
        existing_backends = {backend.name: backend.is_available() for backend in self._raw_params["REPORTING_BACKENDS"]}
        if self._raw_params["REPORTING_BACKENDS_ACTIVE"] != None:
            for active_backend in self._raw_params["REPORTING_BACKENDS_ACTIVE"]:
                if active_backend in existing_backends:
                    if not existing_backends[active_backend]:
                        _param_error("REPORTING_BACKENDS_ACTIVE",
                            "backend '%s' is not available (available backends are: %s)" % (
                                active_backend, ", ".join([backend for backend, available in existing_backends.items() if available])
                        ))
                else:
                    _param_error("REPORTING_BACKENDS_ACTIVE",
                        "backend '%s' does not exist (backends are: %s)" % (
                            active_backend, ", ".join(existing_backends.keys())
                    ))
        else:
            self._raw_params["REPORTING_BACKENDS_ACTIVE"] = [
                backend for backend, is_available in existing_backends.items() if is_available  
            ]
    
    def get_project_dir(self):
        return self._project_dir
        
    def _get_param(self, name, checker, is_list=False, is_dict=False, required=True, default=None):
        if not hasattr(self._settings, name):
            if required:
                _param_error(name, "required parameter is missing")
            else:
                return default
            
        value = getattr(self._settings, name)

        if is_list:
            if type(value) not in (list, tuple):
                _param_error(name, "parameter must be a list or a tuple")
            for v in value:
                error = checker(name, v)
                if error:
                    _param_error(name, error)
            value = list(value) # convert tuple in list
        elif is_dict:
            if type(value) != dict:
                _param_error(name, "parameter must be a dict")
            for v in value.values():
                error = checker(name, v)
                if error:
                    _param_error(name, error)
        
        else:
            error = checker(name, value)
            if error:
                _param_error(name, error)

        return value
    
    def get_cli_extra_args_callback(self):
        return self._raw_params["CLI_EXTRA_ARGS"]
    
    def add_cli_extra_args(self, cli_args_parser):
        callback = self.get_cli_extra_args_callback()
        if callback:
            group = cli_args_parser.add_argument_group("Project custom options")
            callback(group)
    
    def get_report_dir_creation_callback(self):
        return self._raw_params["REPORT_DIR_CREATION"]
    
    def get_testsuites(self, check_metadata_policy=True):
        suites = self._raw_params["TESTSUITES"]
        policy = self.get_metadata_policy()
        if check_metadata_policy and policy:
            policy.check_suites_compliance(suites)
        return suites

    def get_fixtures(self):
        return self._raw_params["FIXTURES"]
    
    def _get_reporting_backends(self):
        return self._raw_params["REPORTING_BACKENDS"]

    def get_reporting_backends(self, capabilities=0, active_only=False):
        if active_only:
            backends = filter(lambda b: b.name in self.get_active_reporting_backend_names(), self._get_reporting_backends())
        else:
            backends = self._get_reporting_backends()
        return list(filter(
            lambda b: b.get_capabilities() & capabilities == capabilities, backends
        ))
    
    def get_active_reporting_backend_names(self):
        return self._raw_params["REPORTING_BACKENDS_ACTIVE"]

    def is_reporting_backend_active(self, backend_name):
        return backend_name in self.get_active_reporting_backend_names()
    
    def get_metadata_policy(self):
        return self._raw_params["METADATA_POLICY"]
    
    def get_before_test_run_hook(self):
        return self._raw_params["RUN_HOOK_BEFORE_TESTS"]

    def get_after_test_run_hook(self):
        return self._raw_params["RUN_HOOK_AFTER_TESTS"]

def create_project(project_dir):
    p = os.path
    shutil.copyfile(get_resource_path(p.join("project", "template.py")), p.join(project_dir, PROJECT_SETTINGS_FILE))
    os.mkdir(p.join(project_dir, "tests"))
    os.mkdir(p.join(project_dir, "fixtures"))

def load_project(project_dir):
    return Project(os.path.join(project_dir, PROJECT_SETTINGS_FILE))
