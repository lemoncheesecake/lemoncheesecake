import time

from lemoncheesecake.reporting import Report, SuiteData, TestData

NOW = time.time()


def _make_tree_node_attrs(name, kwargs):
    return {
        "description": kwargs.get("description", name.title()),
        "tags": kwargs.get("tags", []),
        "properties": kwargs.get("properties", {}),
        "links": kwargs.get("links", [])
    }


class TreeNodeMockup:
    def __init__(self, name, description, tags, properties, links):
        self.name = name
        self.description = description
        self.tags = tags[:]
        self.properties = dict(properties)
        self.links = links[:]


class TestMockup(TreeNodeMockup):
    def __init__(self, name, description, tags, properties, links, status):
        TreeNodeMockup.__init__(self, name, description, tags, properties, links)
        self.status = status


def tst_mockup(name, **kwargs):
    attrs = _make_tree_node_attrs(name, kwargs)
    attrs["status"] = kwargs.get("status", "passed")

    return TestMockup(name, **attrs)


class SuiteMockup(TreeNodeMockup):
    def __init__(self, name, **kwargs):
        TreeNodeMockup.__init__(self, name, **kwargs)
        self.suites = []
        self.tests = []

    def add_test(self, test):
        self.tests.append(test)
        return self

    def add_suite(self, suite):
        self.suites.append(suite)
        return self


def suite_mockup(name, **kwargs):
    return SuiteMockup(name, **_make_tree_node_attrs(name, kwargs))


class ReportMockup:
    def __init__(self):
        self.suites = []

    def add_suite(self, suite):
        self.suites.append(suite)
        return self


def report_mockup():
    return ReportMockup()


def make_test_data_from_mockup(mockup):
    data = TestData(mockup.name, mockup.description)
    data.status = mockup.status
    data.start_time = NOW
    data.end_time = NOW
    return data


def make_suite_data_from_mockup(mockup):
    data = SuiteData(mockup.name, mockup.description)
    for test_mockup in mockup.tests:
        data.add_test(make_test_data_from_mockup(test_mockup))
    for sub_suite_mockup in mockup.suites:
        data.add_suite(make_suite_data_from_mockup(sub_suite_mockup))
    return data


def make_report_from_mockup(mockup):
    report = Report()
    report.start_time = NOW
    report.end_time = NOW
    report.report_generation_time = NOW
    for suite_mockup in mockup.suites:
        report.add_suite(make_suite_data_from_mockup(suite_mockup))
    return report
