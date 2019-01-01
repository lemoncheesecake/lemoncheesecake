from __future__ import print_function

from terminaltables import AsciiTable


def print_table(title, headers, lines):
    if lines:
        print("%s:" % title)
        print(AsciiTable([headers] + lines).table)
    else:
        print("%s: <none>" % title)
    print()
