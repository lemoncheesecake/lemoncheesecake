import os
from contextlib import contextmanager


def _apply_vars(new_vars):
    for name, value in new_vars.items():
        if value is not None:
            os.environ[name] = value
        else:
            if name in os.environ:
                del os.environ[name]


@contextmanager
def env_vars(**new_vars):
    old_vars = {name: os.environ.get(name) for name in new_vars}

    _apply_vars(new_vars)
    try:
        yield

    finally:
        _apply_vars(old_vars)


@contextmanager
def change_dir(new_dir):
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(old_dir)
