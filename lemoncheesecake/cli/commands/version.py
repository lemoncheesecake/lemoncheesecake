from __future__ import print_function

from lemoncheesecake.cli.utils import LEMONCHEESECAKE_VERSION
from lemoncheesecake.cli.command import Command


class VersionCommand(Command):
    def get_name(self):
        return "version"

    def get_description(self):
        return "Show lemoncheesecake version"

    def run_cmd(self, cli_args):
        print(LEMONCHEESECAKE_VERSION)
        return 0
