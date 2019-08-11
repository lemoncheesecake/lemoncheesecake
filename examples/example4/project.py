import os.path

from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suites_from_directory

###
# Variables
###
project_dir = os.path.dirname(__file__)


###
# Project
###
class MyProject(Project):
    def load_suites(self):
        return load_suites_from_directory(os.path.join(self.dir, "tests"))


project = MyProject(project_dir)
