#!/usr/bin/python

'''
Created on Aug 20, 2016

@author: nicolas
'''

from setuptools import setup, find_packages

setup(
    name = "lemoncheesecake",
    version = "0.4.0",
    packages = find_packages(),
    include_package_data = True,
    install_requires = ["colorama", "termcolor"],
    extras_require = {
        "xml": "lxml"
    },
    entry_points={
        "console_scripts": [
            "lcc-run = lemoncheesecake.commands.run:run",
            "lcc-create-project = lemoncheesecake.commands.create_project:create_project"
        ]
    }
)