'''
Created on Sep 8, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import InvalidMetadataError

__all__ = ("PropertyValidator",)

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
                    raise InvalidMetadataError(
                        "cannot load %s '%s', the property '%s' is not supported (availables are: %s)" % (
                        obj_type, obj.id, property_name, ", ".join(accepted)
                    ))
        
        for mandatory in [ m for m in rules.keys() if rules[m]["mandatory"] ]:
            if not mandatory in obj.properties.keys():
                raise InvalidMetadataError(
                    "cannot load %s '%s', the mandatory property '%s' is missing" % (
                    obj_type, obj.id, mandatory
                ))
        
        for name, value in obj.properties.items():
            if not name in rules:
                continue
            if rules[name]["accepted_values"] and not value in rules[name]["accepted_values"]:
                raise InvalidMetadataError(
                    "cannot load %s '%s', value '%s' of property '%s' is not among accepted values: %s" % (
                    obj_type, obj.id, value, name, rules[name]["accepted_values"]
                ))
            
    def check_test_compliance(self, test):
        self._check_compliance(test, "test", self._test_rules, self._accepted_test_properties)

    def check_suite_compliance(self, suite):
        self._check_compliance(suite, "suite", self._suite_rules, self._accepted_suite_properties)
