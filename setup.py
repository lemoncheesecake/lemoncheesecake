#!/usr/bin/python

'''
Created on Aug 20, 2016

@author: nicolas
'''

from setuptools import setup, find_packages

setup(
    name = "lemoncheesecake",
    version = "0.10.3",
    description = "A framework for functional QA testing",
    author = "Nicolas Delon",
    author_email = "nicolas.delon@gmail.com",
    license="Apache License (Version 2.0)",
    url = "https://github.com/lemoncheesecake",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords = "QA tests functional",

    packages = find_packages(),
    include_package_data = True,
    install_requires = ["colorama", "termcolor", "terminaltables"],
    extras_require = {
        "xml": "lxml",
        "junit": "lxml"
    },
    entry_points={
        "console_scripts": [
            "lcc = lemoncheesecake.cli:main",
        ]
    }
)
