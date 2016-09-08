import fnmatch
import inspect

from lemoncheesecake.exceptions import LemonCheesecakeException, LemonCheesecakeInternalError
from lemoncheesecake.runtime import get_runtime

__all__ = (
    # messages & steps
    "log_debug", "log_info", "log_warn", "log_error", "set_step",
    # attachments
    "prepare_attachment", "save_attachment_file", "save_attachment_content",
    # decorators
    "test", "tags", "prop", "url", "suite_rank",
    # testsuite
    "Test", "TestSuite",
    # exceptions
    "AbortTest", "AbortTestSuite", "AbortAllTests"
)

###
# Shortcuts for tests
###

def log_debug(content):
    """
    Add a debug message.
    """
    get_runtime().log_debug(content)

def log_info(content):
    """
    Add a info message.
    """
    get_runtime().log_info(content)

def log_warn(content):
    """
    Add a warning message.
    """
    get_runtime().log_warn(content)

def log_error(content):
    """
    Add an error message.
    """
    get_runtime().log_error(content)

def set_step(description):
    """
    Add a new step.
    """
    get_runtime().set_step(description)

def prepare_attachment(filename, description=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return get_runtime().prepare_attachment(filename, description)

def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    get_runtime().save_attachment_file(filename, description)

def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description)

###
# Exception classes
###

class CannotLoadTest(LemonCheesecakeException):
    message_prefix = "Cannot load test"

class CannotLoadTestSuite(LemonCheesecakeException):
    message_prefix = "Cannot load testsuite"

class PropertyError(LemonCheesecakeException):
    message_prefix = "Property error"

class AbortTest(LemonCheesecakeException):
    message_prefix = "The test has been aborted"
    
    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)
    
class AbortTestSuite(LemonCheesecakeException):
    message_prefix = "The testsuite has been aborted"

    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)

class AbortAllTests(LemonCheesecakeException):
    message_prefix = "All tests have been aborted"

    def __init__(self, reason):
        LemonCheesecakeException.__init__(self, reason)

###
# Property validator
###

class PropertyValidator:
    def __init__(self):
        self._test_rules = {}
        self._suite_rules = {}
        self._accepted_test_properties = None
        self._accepted_suite_properties = None
    
    def _add_rule(self, rules, property_name, rule_name, rule_value):
        if property_name not in rules:
            rules[property_name] = { "mandatory": False, "accepted_values": [] }
        rules[property_name][rule_name] = rule_value

    def set_accepted_test_properties(self, names):
        self._accepted_test_properties = names
    
    def set_accepted_suite_properties(self, names):
        self._accepted_suite_properties = names
    
    def make_test_property_mandatory(self, name):
        self._add_rule(self._test_rules, name, "mandatory", True)
    
    def set_test_property_accepted_values(self, name, values):
        self._add_rule(self._test_rules, name, "accepted_values", values)
    
    def make_suite_property_mandatory(self, name):
        self._add_rule(self._suite_rules, name, "mandatory", True)
    
    def set_suite_property_accepted_values(self, name, values):
        self._add_rule(self._suite_rules, name, "accepted_values", values)
    
    def _check_compliance(self, obj, obj_type, rules, accepted):
        if accepted != None:
            for property_name in obj.properties.keys():
                if not property_name in accepted:
                    raise PropertyError("cannot load %s '%s', the property '%s' is not supported (availables are: %s)",
                                        obj_type, obj.id, property_name, ", ".join(accepted))
        
        for mandatory in [ m for m in rules.keys() if rules[m]["mandatory"] ]:
            if not mandatory in obj.properties.keys():
                raise PropertyError("cannot load %s '%s', the mandatory property '%s' is missing" % (obj_type, obj.id, mandatory))
        
        for name, value in obj.properties.items():
            if not name in rules:
                continue
            if rules[name]["accepted_values"] and not value in rules[name]["accepted_values"]:
                raise PropertyError(
                    "cannot load %s '%s', value '%s' of property '%s' is not among accepted values: %s" % (obj_type, obj.id, value, name, rules[name]["accepted_values"])
                )
            
    def check_test_compliance(self, test):
        self._check_compliance(test, "test", self._test_rules, self._accepted_test_properties)

    def check_suite_compliance(self, suite):
        self._check_compliance(suite, "suite", self._suite_rules, self._accepted_suite_properties)

###
# Test, TestSuite classes and decorators
###

FILTER_SUITE_MATCH_ID = 0x01
FILTER_SUITE_MATCH_DESCRIPTION = 0x02
FILTER_SUITE_MATCH_TAG = 0x04
FILTER_SUITE_MATCH_URL_NAME = 0x08
FILTER_SUITE_MATCH_PROPERTY = 0x10

class Filter:
    def __init__(self):
        self.test_id = []
        self.test_description = []
        self.testsuite_id = []
        self.testsuite_description = []
        self.tags = [ ]
        self.properties = {}
        self.url_names = [ ]
    
    def is_empty(self):
        count = 0
        for value in self.test_id, self.testsuite_id, self.test_description, \
            self.testsuite_description, self.tags, self.properties, self.url_names:
            count += len(value)
        return count == 0
    
    def get_flags_to_match_testsuite(self):
        flags = 0
        if self.testsuite_id:
            flags |= FILTER_SUITE_MATCH_ID
        if self.testsuite_description:
            flags |= FILTER_SUITE_MATCH_DESCRIPTION
        return flags
    
    def match_test(self, test, parent_suite_match=0):
        match = False
        
        if self.test_id:
            for id in self.test_id:
                if fnmatch.fnmatch(test.id, id):
                    match = True
                    break
            if not match:
                return False
        
        if self.test_description:
            for desc in self.test_description:
                if fnmatch.fnmatch(test.description, desc):
                    match = True
                    break
            if not match:
                return False
        
        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(test.tags, tag):
                    match = True
                    break
            if not match:
                return False
                
        if self.properties and not parent_suite_match & FILTER_SUITE_MATCH_PROPERTY:
            for key, value in self.properties.items():
                if key in test.properties and test.properties[key] == value:
                    match = True
                    break
            if not match:
                return False
                
        if self.url_names and not parent_suite_match & FILTER_SUITE_MATCH_URL_NAME:
            for url in self.url_names:
                if url in [ u[1] for u in test.urls if u[1] ]:
                    match = True
                    break
            if not match:
                return False
        
        return True
    
    def match_testsuite(self, suite, parent_suite_match=0):
        match = 0
        
        if self.testsuite_id and not parent_suite_match & FILTER_SUITE_MATCH_ID:
            for id in self.testsuite_id:
                if fnmatch.fnmatch(suite.id, id):
                    match |= FILTER_SUITE_MATCH_ID
                    break
                
        if self.testsuite_description and not parent_suite_match & FILTER_SUITE_MATCH_DESCRIPTION:
            for desc in self.testsuite_description:
                if fnmatch.fnmatch(suite.description, desc):
                    match |= FILTER_SUITE_MATCH_DESCRIPTION
                    break

        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(suite.tags, tag):
                    match |= FILTER_SUITE_MATCH_TAG
                    break

        if self.properties and not parent_suite_match & FILTER_SUITE_MATCH_PROPERTY:
            for key, value in self.properties.items():
                if key in suite.properties and suite.properties[key] == value:
                    match |= FILTER_SUITE_MATCH_PROPERTY
                    break

        if self.url_names and not parent_suite_match & FILTER_SUITE_MATCH_URL_NAME:
            for url in self.url_names:
                if url in [ u[0] for u in suite.urls ]:
                    match |= FILTER_SUITE_MATCH_URL_NAME
                    break

        return match

class Test:
    test_current_rank = 1

    def __init__(self, id, description, callback, force_rank=None):
        self.id = id
        self.description = description
        self.callback = callback
        self.tags = [ ]
        self.properties = {}
        self.urls = [ ]
        self.rank = force_rank if force_rank != None else Test.test_current_rank
        Test.test_current_rank += 1
        
    def __str__(self):
        return "%s (%s) # %d" % (self.id, self.description, self.rank)
        
class StaticTestDecorator:
    def __init__(self, description):
        self.description = description
    
    def __call__(self, callback):
        callback = callback
        id = callback.__name__
        
        return Test(id, self.description, callback)

def test(description): # decorator shortcut
    return StaticTestDecorator(description)

def tags(*tag_names):
    def wrapper(obj):
        if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
            raise LemonCheesecakeInternalError("Tags can only be added to Test and TestSuite objects (got %s)" % type(obj))
        obj.tags = tag_names
        return obj
    return wrapper

def prop(key, value):
    def wrapper(obj):
        if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
            raise LemonCheesecakeInternalError("Property can only be added to Test and TestSuite objects (got %s)" % type(obj))
        obj.properties[key] = value
        return obj
    return wrapper

def suite_rank(value):
    def wrapper(klass):
        klass._rank = value
        return klass
    return wrapper

def url(url, name=None):
    def wrapper(obj):
        if (inspect.isclass(obj) and not issubclass(obj, TestSuite)) and not isinstance(obj, Test):
            raise LemonCheesecakeInternalError("URLs can only be added to Test and TestSuite objects (got %s)" % type(obj))
        obj.urls.append([url, name])
        return obj
    return wrapper

class TestSuite:
    tags = [ ]
    properties = {}
    urls = [ ]
    sub_testsuite_classes = [ ]        
    
    def load(self, parent_suite=None):
        self.parent_suite = parent_suite
        
        # suite id & description
        if not hasattr(self, "id"):
            self.id = self.__class__.__name__
        if not hasattr(self, "description"):
            self.description = self.__class__.__name__

        # static tests
        self._tests = [ ]
        for attr in dir(self):
            obj = getattr(self, attr)
            if isinstance(obj, Test):
                self.assert_test_description_is_unique(obj.description)
                self._tests.append(obj)
        self._tests = sorted(self._tests, key=lambda x: x.rank)

        # dynamic test        
        self.load_generated_tests()
        
        self._sub_testsuites = [ ]
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if not inspect.isclass(attr) or not issubclass(attr, TestSuite):
                continue
            sub_suite = attr()
            sub_suite.load(self)
            self.assert_sub_test_suite_description_is_unique(sub_suite.description)
            self._sub_testsuites.append(sub_suite)

        # filtering data
        self._selected_test_ids = [ t.id for t in self._tests ]
    
    def get_path(self):
        suites = [ self ]
        parent_suite = self.parent_suite
        while parent_suite != None:
            suites.insert(0, parent_suite)
            parent_suite = parent_suite.parent_suite
        return suites
    
    def get_path_str(self, sep=">"):
        return (" %s " % sep).join([ s.id for s in self.get_path() ])
    
    def __str__(self):
        return self.get_path_str()
    
    def get_depth(self):
        depth = 1
        parent = self.parent_suite
        while parent:
            depth += 1
            parent = parent.parent_suite
        return depth
    
    def assert_test_description_is_unique(self, description):
        result = list(filter(lambda t: t.description == description, self._tests))
        if result:
            raise CannotLoadTest(
                "a test with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def assert_sub_test_suite_description_is_unique(self, description):
        result = list(filter(lambda s: s.description == description, self._sub_testsuites))
        if result:
            raise CannotLoadTestSuite(
                "a sub test suite with description '%s' is already registered in test suite %s" % (description, self.get_path_str())
            )
        
    def load_generated_tests(self):
        pass
    
    def get_tests(self, filtered=True):
        if filtered:
            return filter(lambda t: self.is_test_selected(t), self._tests)
        else:
            return self._tests
    
    def get_sub_testsuites(self, filtered=True):
        if filtered:
            return filter(lambda s: s.has_selected_tests(deep=True), self._sub_testsuites)
        else:
            return self._sub_testsuites
    
    def get_suite_id(self):
        return self.id
    
    def get_suite_description(self):
        return self.description
    
    def register_test(self, new_test, before_test=None, after_test=None):
        if before_test and after_test:
            raise Exception("before_test and after_test are mutually exclusive")
        
        self.assert_test_description_is_unique(new_test.description)
        
        ref_test_id = before_test if before_test else after_test
        
        if ref_test_id:
            # find test corresponding to before_test/after_test
            ref_test, ref_test_idx = None, None
            for idx, test in enumerate(self._tests):
                if test.id == ref_test_id:
                    ref_test, ref_test_idx = test, idx
                    break
            if ref_test_idx == None:
                raise CannotLoadTest("Could not find any test named '%s' in the test suite '%s'" % (ref_test_id, self.get_suite_id()))
            
            # set the test appropriate rank and shift all test's ranks coming after the new test
            new_test.rank = ref_test.rank + (1 if after_test else 0)
            for test in self._tests[ref_test_idx + (1 if after_test else 0):]:
                test.rank += 1
            self._tests.insert(ref_test_idx + (1 if after_test else 0), new_test)
        else:
            self._tests.append(new_test)
    
    def register_tests(self, tests, before_test=None, after_test=None):
        if before_test and after_test:
            raise Exception("before_test and after_test are mutually exclusive")
        
        if after_test:
            previous_test = after_test
            for test in tests:
                self.register_test(test, after_test=previous_test)
                previous_test = test.id
        else:
            for test in tests:
                self.register_test(test, before_test=before_test)
    
    ###
    # Filtering methods
    ###
    
    def apply_filter(self, filter, parent_suite_match=0):
        self._selected_test_ids = [ ]
        
        suite_match = filter.match_testsuite(self, parent_suite_match)
        suite_match |= parent_suite_match
        
        if suite_match & filter.get_flags_to_match_testsuite() == filter.get_flags_to_match_testsuite():
            for test in self._tests:
                test_match = filter.match_test(test, suite_match)
                if test_match:
                    self._selected_test_ids.append(test.id)
        
        for suite in self._sub_testsuites:
            suite.apply_filter(filter, suite_match)

    def has_selected_tests(self, deep=True):
        if deep:
            if self._selected_test_ids:
                return True
             
            for suite in self._sub_testsuites:
                if suite.has_selected_tests():
                    return True
             
            return False
        else:
            return bool(self._selected_test_ids)
    
    def is_test_selected(self, test):
        return test.id in self._selected_test_ids
    
    ###
    # Hooks
    ###
    
    def before_suite(self):
        pass
    
    def after_suite(self):
        pass

    def before_test(self, test_name):
        pass
    
    def after_test(self, test_name):
        pass