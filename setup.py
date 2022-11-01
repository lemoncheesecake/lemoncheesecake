#!/usr/bin/python

from setuptools import setup, find_packages

import lemoncheesecake


setup(
    name="lemoncheesecake",
    version=lemoncheesecake.__version__,
    description="Test Storytelling",
    long_description=open("README.rst").read(),
    author="Nicolas Delon",
    author_email="nicolas.delon@gmail.com",
    license="Apache License (Version 2.0)",
    url="http://lemoncheesecake.io",
    python_requires='>=3.7',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
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
    install_requires=("colorama", "termcolor", "terminaltables", "typing", "python-slugify"),
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
