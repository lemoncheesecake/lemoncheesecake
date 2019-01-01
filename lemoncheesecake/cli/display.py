'''
Created on Mar 12, 2017

@author: nicolas
'''

from __future__ import print_function

from termcolor import colored


def bold(s):
    return colored(s, attrs=["bold"])
