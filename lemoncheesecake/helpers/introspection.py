import inspect

import six

from lemoncheesecake.exceptions import ProgrammingError


def object_has_method(obj, method_name):
    try:
        return callable(getattr(obj, method_name))
    except AttributeError:
        return False


def get_callable_args(cb):
    if not inspect.isroutine(cb):
        try:
            cb = getattr(cb, "__call__")
        except AttributeError:
            raise ProgrammingError("%s is not something that can be called" % cb)

    spec = inspect.getfullargspec(cb) if six.PY3 else inspect.getargspec(cb)
    args_start = 1 if inspect.ismethod(cb) else 0
    return spec.args[args_start:]
