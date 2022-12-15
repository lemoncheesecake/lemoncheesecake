'''
Created on Oct 29, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.metadatapolicy import MetadataPolicy
from lemoncheesecake.exceptions import ValidationError


def test_property_value_validation():
    @lcc.prop("foo", "1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("foo", "2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", ("1", "2"), on_test=True, on_suite=True)
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", ("3", "4"), on_test=True, on_suite=True)
    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_required_property():
    @lcc.prop("foo", "1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("foo", "2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", on_test=True, on_suite=True, required=True)
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.add_property_rule("bar", on_test=True, on_suite=True, required=True)
    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_allowed_properties_and_tags():
    @lcc.prop("foo", "1")
    @lcc.tags("tag1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("foo", "2")
        @lcc.tags("tag2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", on_test=True, on_suite=True)
    policy.add_tag_rule(["tag1", "tag2"], on_test=True, on_suite=True)
    policy.disallow_unknown_properties()
    policy.disallow_unknown_tags()
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.add_property_rule("bar", on_test=True, on_suite=True)
    policy.add_tag_rule(["tag3"], on_test=True, on_suite=True)
    policy.disallow_unknown_properties()
    policy.disallow_unknown_tags()

    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_different_test_and_suite_property_configurations():
    @lcc.prop("foo", "1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("bar", "2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", on_suite=True)
    policy.add_property_rule("bar", on_test=True)
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.add_property_rule("foo", on_test=True)
    policy.add_property_rule("bar", on_suite=True)

    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_different_test_and_suite_tag_configurations():
    @lcc.tags("tag1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.tags("tag2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.add_tag_rule("tag1", on_suite=True)
    policy.add_tag_rule("tag2", on_test=True)
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.add_tag_rule("tag1", on_test=True)
    policy.add_tag_rule("tag2", on_suite=True)

    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_disallow_unknown_property():
    @lcc.prop("foo", "1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("bar", "2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.disallow_unknown_properties()

    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)


def test_disallow_unknown_tag():
    @lcc.tags("tag1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.tags("tag2")
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    # passing case
    policy = MetadataPolicy()
    policy.check_test_compliance(suite.get_tests()[0])
    policy.check_suite_compliance(suite)

    # non-passing case
    policy = MetadataPolicy()
    policy.disallow_unknown_tags()

    with pytest.raises(ValidationError):
        policy.check_test_compliance(suite.get_tests()[0])
    with pytest.raises(ValidationError):
        policy.check_suite_compliance(suite)
