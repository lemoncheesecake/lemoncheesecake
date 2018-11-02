import os.path

from lemoncheesecake.project import SimpleProjectConfiguration

###
# Variables
###
project_dir = os.path.dirname(__file__)


###
# Project
###
class MyProjectConfiguration(SimpleProjectConfiguration):
    def get_report_info(self):
        return SimpleProjectConfiguration.get_report_info(self) + [["foo", "bar"]]


project = MyProjectConfiguration(
    suites_dir=os.path.join(project_dir, "suites"),
    fixtures_dir=os.path.join(project_dir, "fixtures"),
    report_title="Awesome report"
)
