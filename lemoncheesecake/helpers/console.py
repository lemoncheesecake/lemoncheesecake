from __future__ import print_function

from terminaltables import AsciiTable
from termcolor import colored


def print_table(title, headers, lines):
    if lines:
        print("%s:" % title)
        print(AsciiTable([headers] + lines).table)
    else:
        print("%s: <none>" % title)
    print()


def bold(s):
    return colored(s, attrs=["bold"])
