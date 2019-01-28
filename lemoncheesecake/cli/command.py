'''
Created on Mar 12, 2017

@author: nicolas
'''


class Command(object):
    def get_name(self):
        pass

    def get_description(self):
        return None

    def add_cli_args(self, cli_parser):
        pass

    def run_cmd(self, cli_args):
        pass
