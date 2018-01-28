import time

from lemoncheesecake.reporting import Report, SuiteData, TestData, StepData, LogData, CheckData

NOW = time.time()


def _make_tree_node_attrs(name, kwargs):
    return {
        "description": kwargs.get("description", name.title()),
        "tags": kwargs.get("tags", []),
        "properties": kwargs.get("properties", {}),
        "links": kwargs.get("links", [])
    }


class StepMockup:
    def __init__(self, description):
        self.description = description
        self._entries = []

    @property
    def entries(self):
        return self._entries

    def add_check(self, outcome):
        self._entries.append(CheckData("check description", outcome=outcome))
        return self

    def _add_log(self, level, message):
        self._entries.append(LogData(level, message, NOW))
        return self

    def add_info_log(self, message="info log"):
        return self._add_log("info", message)

    def add_error_log(self, message="error log"):
        return self._add_log("error", message)


def step_mockup(description="step"):
    return StepMockup(description)


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
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)
        return self


_test_counter = 1


def tst_mockup(name=None, **kwargs):
    global _test_counter

    if name is None:
        name = "test_%d" % _test_counter
        _test_counter += 1

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


_suite_counter = 1


def suite_mockup(name=None, **kwargs):
    global _suite_counter

    if name is None:
        name = "suite_%d" % _suite_counter
        _suite_counter += 1

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
    for step_mockup in mockup.steps:
        step = StepData(step_mockup.description)
        data.steps.append(step)
        for entry in step_mockup.entries:
            step.entries.append(entry)
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
