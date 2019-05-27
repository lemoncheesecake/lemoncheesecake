import time

from lemoncheesecake.reporting import Report, Result, SuiteResult, TestResult, Step, Log, Check

NOW = time.time()


def _make_tree_node_attrs(name, kwargs):
    return {
        "description": kwargs.get("description", name.title()),
        "tags": kwargs.get("tags", []),
        "properties": kwargs.get("properties", {}),
        "links": kwargs.get("links", []),
        "start_time": kwargs.get("start_time", None),
        "end_time": kwargs.get("end_time", None)
    }


class StepMockup:
    def __init__(self, description, start_time, end_time):
        self.description = description
        self._entries = []
        self.start_time = start_time
        self.end_time = end_time

    @property
    def entries(self):
        return self._entries

    def add_check(self, is_successful):
        self._entries.append(Check("check description", is_successful=is_successful, details=None, ts=NOW))
        return self

    def _add_log(self, level, message):
        self._entries.append(Log(level, message, NOW))
        return self

    def add_info_log(self, message="info log"):
        return self._add_log("info", message)

    def add_error_log(self, message="error log"):
        return self._add_log("error", message)


def step_mockup(description="step", start_time=None, end_time=None):
    return StepMockup(description, start_time, end_time)


def make_step_data_from_mockup(mockup):
    data = Step(mockup.description)
    data.start_time = mockup.start_time
    data.end_time = mockup.end_time
    for entry in mockup.entries:
        data.entries.append(entry)
    return data


class TreeNodeMockup:
    def __init__(self, name, description, tags, properties, links, start_time, end_time):
        self.name = name
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.tags = tags[:]
        self.properties = dict(properties)
        self.links = links[:]


class TestMockup(TreeNodeMockup):
    def __init__(self, name, description, tags, properties, links, status, start_time, end_time):
        TreeNodeMockup.__init__(self, name, description, tags, properties, links, start_time, end_time)
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


class HookMockup(object):
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)
        return self


def hook_mockup(start_time=None, end_time=None):
    return HookMockup(start_time, end_time)


def make_hook_data_from_mockup(mockup):
    if mockup is None:
        return None

    data = Result()
    data.start_time = mockup.start_time if mockup.start_time is not None else NOW
    data.end_time = mockup.end_time if mockup.end_time is not None else NOW
    for step_mockup in mockup.steps:
        data.steps.append(make_step_data_from_mockup(step_mockup))
    return data


class SuiteMockup(TreeNodeMockup):
    def __init__(self, name, **kwargs):
        TreeNodeMockup.__init__(self, name, **kwargs)
        self.setup = None
        self.teardown = None
        self.suites = []
        self.tests = []

    def add_setup(self, setup):
        self.setup = setup
        return self

    def add_teardown(self, teardown):
        self.teardown = teardown
        return self

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
    data = TestResult(mockup.name, mockup.description)
    data.status = mockup.status
    data.start_time = mockup.start_time if mockup.start_time is not None else NOW
    data.end_time = mockup.end_time if mockup.end_time is not None else NOW
    for step_mockup in mockup.steps:
        data.steps.append(make_step_data_from_mockup(step_mockup))
    return data


def make_suite_data_from_mockup(mockup):
    data = SuiteResult(mockup.name, mockup.description)
    data.start_time = mockup.start_time if mockup.start_time is not None else NOW
    data.end_time = mockup.end_time if mockup.end_time is not None else NOW
    data.suite_setup = make_hook_data_from_mockup(mockup.setup)
    data.suite_teardown = make_hook_data_from_mockup(mockup.teardown)
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
