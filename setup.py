#!/usr/bin/python

'''
Created on Aug 20, 2016

@author: nicolas
'''

import sys
from setuptools import setup, find_packages

import lemoncheesecake

install_requires = ["colorama", "termcolor", "terminaltables", "six", "typing"]
# slugify 5.0 and higher does no longer support Python 2.7 anymore.
# Installing slugify using Python 2.7 unfortunately does not install a supported version of slugify,
# meaning we must manually pick the right version ourself.
if sys.version_info[0] == 2:
    install_requires.append("python-slugify~=4.0.1")
else:
    install_requires.append("python-slugify")

setup(
    name="lemoncheesecake",
    version=lemoncheesecake.__version__,
    description="Test Storytelling",
    long_description=open("README.rst").read(),
    author="Nicolas Delon",
    author_email="nicolas.delon@gmail.com",
    license="Apache License (Version 2.0)",
    url="http://lemoncheesecake.io",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    keywords="QA tests functional",
    project_urls={
        'Documentation': 'http://docs.lemoncheesecake.io/',
        'Source': 'https://github.com/lemoncheesecake/lemoncheesecake',
        'Tracker': 'https://github.com/lemoncheesecake/lemoncheesecake/issues',
    },

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        "xml": "lxml",
        "junit": "lxml",
        "reportportal": "reportportal-client~=3.0",
        "slack": "slacker"
    },
    entry_points={
        "console_scripts": [
            "lcc = lemoncheesecake.cli:main",
        ]
    }
)
