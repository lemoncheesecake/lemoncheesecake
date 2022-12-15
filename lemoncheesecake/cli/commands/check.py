from lemoncheesecake.project import load_project, PreparedProject
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import add_project_cli_arg


class CheckCommand(Command):
    def get_name(self):
        return "check"

    def get_description(self):
        return "Check if the project is valid (project module, suites, fixtures, metadata policy)"

    def add_cli_args(self, cli_parser):
        add_project_cli_arg(cli_parser)

    def run_cmd(self, cli_args):
        project = load_project(cli_args.project)
        PreparedProject.create(project)

        print("Everything is ok")
