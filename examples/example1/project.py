import os.path

from lemoncheesecake.project import Project

###
# Variables
###
project_dir = os.path.dirname(__file__)


###
# Project
###
class MyProject(Project):
    def get_report_info(self):
        return Project.get_report_info(self) + [["foo", "bar"]]


project = MyProject(project_dir)
project.report_title = "Awesome report"
project.hide_command_line_in_report = True
