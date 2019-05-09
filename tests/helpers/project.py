import lemoncheesecake.api as lcc
from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suite_from_class


class DummyProject(Project):
    def __init__(self, project_dir, suites):
        Project.__init__(self, project_dir)
        self.suites = suites

    def get_suites(self):
        return self.suites

    def create_report_dir(self):
        return self.dir

    def get_all_reporting_backends(self):
        return []

    def get_default_reporting_backends_for_test_run(self):
        return []


def build_project(suites, tmpdir):
    return DummyProject(tmpdir.strpath, suites)


@lcc.suite("My Suite")
class mysuite:
    @lcc.test("My Test")
    def mytest(self):
        pass


DUMMY_SUITE = load_suite_from_class(mysuite)
