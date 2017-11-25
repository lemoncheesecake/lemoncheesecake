'''
Created on Jan 25, 2017

@author: nicolas
'''

import argparse

from lemoncheesecake.exceptions import LemonCheesecakeException
from lemoncheesecake.cli.commands import get_commands
from lemoncheesecake.cli.utils import LEMONCHEESECAKE_VERSION


def main(args=None):
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("--version", "-v", action="version", version=LEMONCHEESECAKE_VERSION)
    cli_sub_parsers = cli_parser.add_subparsers(dest="command")
    commands = {cmd.get_name(): cmd for cmd in get_commands()}
    for command in commands.values():
        cli_cmd_parser = cli_sub_parsers.add_parser(command.get_name(), help=command.get_description())
        try:
            command.add_cli_args(cli_cmd_parser)
        except LemonCheesecakeException as e:
            return str(e)

    cli_args = cli_parser.parse_args(args)

    try:
        command = commands[cli_args.command]
    except KeyError:
        return "Unknown command '%s'" % cli_args.command

    try:
        return command.run_cmd(cli_args)
    except LemonCheesecakeException as e:
        return str(e)
