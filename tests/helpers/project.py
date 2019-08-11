import lemoncheesecake.api as lcc
from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suite_from_class


class DummyProject(Project):
    def __init__(self, project_dir, suites):
        Project.__init__(self, project_dir)
        self.suites = suites
        self.reporting_backends = {}
        self.default_reporting_backend_names = []

    def load_suites(self):
        return self.suites

    def create_report_dir(self):
        return self.dir


def build_project(suites, tmpdir):
    return DummyProject(tmpdir.strpath, suites)


@lcc.suite("My Suite")
class mysuite:
    @lcc.test("My Test")
    def mytest(self):
        pass


DUMMY_SUITE = load_suite_from_class(mysuite)
