'''
Created on Mar 12, 2017

@author: nicolas
'''

import sys

import termcolor

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
