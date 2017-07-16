import os.path

from lemoncheesecake.project import SimpleProjectConfiguration


project_dir = os.path.dirname(__file__)
project = SimpleProjectConfiguration(
    suites_dir=os.path.join(project_dir, "suites"),
    fixtures_dir=os.path.join(project_dir, "fixtures"),
)