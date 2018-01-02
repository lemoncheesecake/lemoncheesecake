import time

from lemoncheesecake.reporting import Report, SuiteData, TestData

NOW = time.time()


class TreeNodeMockup:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description if description is not None else name.title()


class TestMockup(TreeNodeMockup):
    def __init__(self, name, description, status):
        TreeNodeMockup.__init__(self, name, description)
        self.status = status


def tst_mockup(name, description=None, status="passed"):
    return TestMockup(name, description, status)


class SuiteMockup(TreeNodeMockup):
    def __init__(self, name, description):
        TreeNodeMockup.__init__(self, name, description)
        self.suites = []
        self.tests = []

    def add_test(self, test):
        self.tests.append(test)
        return self

    def add_suite(self, suite):
        self.suites.append(suite)
        return self


def suite_mockup(name, description=None):
    return SuiteMockup(name, description)


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
