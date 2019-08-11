import os
from contextlib import contextmanager


@contextmanager
def env_var(name, value):
    orig_value = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if orig_value is not None:
            os.environ[name] = orig_value
        else:
            del os.environ[name]
