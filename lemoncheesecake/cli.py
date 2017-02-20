'''
Created on Jan 25, 2017

@author: nicolas
'''

import argparse

class Command:
    def get_name(self):
        pass
    
    def get_description(self):
        return None
    
    def add_cli_args(self, cli_parser):
        pass
    
    def run_cmd(self, cli_args):
        pass

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
    
    return command.run_cmd(cli_args)
