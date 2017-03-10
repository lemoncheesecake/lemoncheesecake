'''
Created on Jan 25, 2017

@author: nicolas
'''

import sys
import argparse

import termcolor

from lemoncheesecake.exceptions import UserError

class Command:
    def __init__(self):
        self.force_color = False
    
    def get_name(self):
        pass
    
    def get_description(self):
        return None
    
    def add_cli_args(self, cli_parser):
        pass
    
    def run_cmd(self, cli_args):
        pass

    def add_color_cli_args(self, cli_parser):
        cli_parser.add_argument("--color", action="store_true", help="Force color printing when command output is redirected")
    
    def process_color_cli_args(self, cli_args):
        self.force_color = cli_args.color
    
    def colored(self, text, color=None, on_color=None, attrs=None):
        if sys.stdout.isatty() or self.force_color:
            return termcolor.colored(text, color, on_color, attrs)
        else:
            return text
    
    def bold(self, text):
        return self.colored(text, attrs=["bold"])
    
def main(args=None):
    from lemoncheesecake.commands import get_commands
    
    cli_parser = argparse.ArgumentParser()
    cli_sub_parsers = cli_parser.add_subparsers(dest="command")
    commands = {cmd.get_name(): cmd for cmd in get_commands()}
    for command in commands.values():
        cli_cmd_parser = cli_sub_parsers.add_parser(command.get_name(), help=command.get_description())
        command.add_cli_args(cli_cmd_parser)
    
    cli_args = cli_parser.parse_args(args)
    
    try:
        command = commands[cli_args.command]
    except KeyError:
        return "Unknown command '%s'" % cli_args.command
    
    try:
        return command.run_cmd(cli_args)
    except UserError as e:
        return str(e)
