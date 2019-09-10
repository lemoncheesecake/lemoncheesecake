'''
Created on Jan 25, 2017

@author: nicolas
'''

from __future__ import print_function
import argparse
import sys

import colorama

from lemoncheesecake.exceptions import LemoncheesecakeException
from lemoncheesecake.cli.commands import get_commands
from lemoncheesecake.cli.utils import LEMONCHEESECAKE_VERSION


# we implement our own "version" instead of using the built-in argparse "version" action
# because its behavior between Python 2 & 3 is not consistent and because it does
# undesired text-wrapping
class Version(argparse.Action):
    def __call__(self, *dummy_args, **dummy_kwargs):
        print(LEMONCHEESECAKE_VERSION)
        sys.exit(0)


def build_cli_parser():
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("--version", "-v", nargs=0, action=Version)
    cli_sub_parsers = cli_parser.add_subparsers(dest="command")
    cli_sub_parsers.required = True
    for command in get_commands():
        cli_cmd_parser = cli_sub_parsers.add_parser(command.get_name(), help=command.get_description())
        command.add_cli_args(cli_cmd_parser)
    return cli_parser


def build_cli_args(args=None):
    cli_parser = build_cli_parser()
    return cli_parser.parse_args(args)


def main(args=None):
    colorama.init()

    try:
        cli_args = build_cli_args(args)
    except LemoncheesecakeException as excp:
        return str(excp)

    command = next(cmd for cmd in get_commands() if cmd.get_name() == cli_args.command)
    try:
        return command.run_cmd(cli_args)
    except LemoncheesecakeException as excp:
        return str(excp)
