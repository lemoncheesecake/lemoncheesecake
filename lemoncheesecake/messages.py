'''
Created on Jan 24, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime

def debug(content):
    get_runtime().debug(content)

def info(content):
    get_runtime().info(content)

def warn(content):
    get_runtime().warn(content)

def error(content):
    get_runtime().error(content)

def step(description):
    get_runtime().step(description)