import lemoncheesecake.api as lcc
from lemoncheesecake.project import ProjectConfiguration, Project
from lemoncheesecake.suite import load_suite_from_class


class DummyProjectConfiguration(ProjectConfiguration):
    def __init__(self, suites):
        self.suites = suites

    def get_suites(self):
        return self.suites

    def create_report_dir(self, top_dir):
        return top_dir

    def get_all_reporting_backends(self):
        return []

    def get_default_reporting_backends_for_test_run(self):
        return []


def build_project(suites, tmpdir):
    return Project(DummyProjectConfiguration(suites), tmpdir.strpath)


@lcc.suite("My Suite")
class mysuite:
    @lcc.test("My Test")
    def mytest(self):
        pass


DUMMY_SUITE = load_suite_from_class(mysuite)
