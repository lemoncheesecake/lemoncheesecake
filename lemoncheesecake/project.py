'''
Created on Mar 12, 2016

@author: nicolas
'''

import imp
import types

from lemoncheesecake.common import LemonCheesecakeException
from lemoncheesecake.testsuite import TestSuite
from lemoncheesecake import reporting

class CannotLoadProjectSettings(LemonCheesecakeException):
    message_prefix = "Cannot load project settings"

class ProjectSettings:
    def __init__(self, project_dir):
        self.project_dir = project_dir
    
    def _check_is_subclass(self, klass):
        def wrapper(name, value):
            if type(value) is not types.ClassType or not issubclass(value, klass):
                return "'%s' has an incorrect value, '%s' is not a subclass of '%s'" % (name, value, klass)
            return None
        return wrapper
    
    def _check_is_type(self, type_):
        def wrapper(name, value):
            if type(value) is not type_:
                return "'%s' has an incorrect value, '%s' is not a '%s'" % (name, value, type_)
            return None
        return wrapper
    
    def _check_is_func(self, name, value):
        if not callable(value):
            return "'%s' has an incorrect value, '%s' is not a function" % (name, value)
        return None
    
    def _check_report_backend(self, name, value):
        if not reporting.has_backend(value):
            return "unknown report backend '%s'" % value
        return None
    
    def _get_param(self, settings, name, checker, is_list=False, is_optional=False, default_value=None):
        if not hasattr(settings, name):
            if is_optional:
                return default_value
            else:
                raise CannotLoadProjectSettings("mandatory parameter '%s' is missing" % name)
            
        value = getattr(settings, name)

        if is_list:
            if type(value) not in (list, tuple):
                raise CannotLoadProjectSettings("parameter '%s' must be a list or a tuple" % name)
            for v in value:
                error = checker(name, v)
                if error:
                    raise CannotLoadProjectSettings(error)
        else:
            error = checker(name, value)
            if error:
                raise CannotLoadProjectSettings(error)
    
        return value
    
    def load(self):
        settings = imp.load_source("settings", "%s/settings.py" % self.project_dir)
        self._testsuites = self._get_param(settings, "TESTSUITES", self._check_is_subclass(TestSuite), is_list=True)
        self.reports_root_dir = self._get_param(settings, "REPORTS_ROOT_DIR", self._check_is_type(str))
        self.report_dir_format = self._get_param(settings, "REPORT_DIR_FORMAT", self._check_is_func)
        self.report_backends = self._get_param(settings, "REPORT_BACKENDS", self._check_report_backend, is_list=True)
    
    def get_testsuite_classes(self):
        return self._testsuites

class Project:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.testsuites = [ ]
        self.testsuites_by_id = { }
        self.tests_by_id = { }
        self.settings = ProjectSettings(self.project_dir)

    def load_settings(self):
        self.settings.load()

    def fetch_testsuite_references(self, suite):
        # process suite
        if suite.id in self.testsuites_by_id:
            raise CannotLoadProjectSettings("A test suite with id '%s' has been registered more than one time" % suite.id)
        self.testsuites_by_id[suite.id] = suite

        # process tests
        for test in suite.get_tests():
            if test.id in self.tests_by_id:
                raise CannotLoadProjectSettings("A test with id '%s' has been registered more than one time" % test.id)
            self.tests_by_id[test.id] = test
        
        # process sub suites
        for sub_suite in suite.get_sub_testsuites():
            self.fetch_testsuite_references(sub_suite)
    
    def load_testsuites(self):
        for suite_class in self.settings.get_testsuite_classes():
            suite = suite_class()
            suite.load()
            self.fetch_testsuite_references(suite)
            self.testsuites.append(suite)