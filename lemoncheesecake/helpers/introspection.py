import inspect

import six


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
            raise ValueError("%s is not something that can be called" % cb)

    spec = inspect.getfullargspec(cb) if six.PY3 else inspect.getargspec(cb)
    args_start = 1 if inspect.ismethod(cb) else 0
    return spec.args[args_start:]


# adapted from https://stackoverflow.com/a/3681323
def _get_unbound_object_attr(obj, attr_name):
    for cls in inspect.getmro(obj.__class__):
        if attr_name in cls.__dict__:
            return cls.__dict__[attr_name]
    raise AttributeError("Cannot find attribute '%s' in %s" % (attr_name, obj))


def _is_property(obj, attr_name):
    try:
        attr = _get_unbound_object_attr(obj, attr_name)
    except AttributeError:
        # there is no such attribute defined in the class, meaning it must be an instance attribute
        # then not a property
        return False
    return isinstance(attr, property)


def _get_class_object_attributes(obj):
    for attr_name in dir(obj):
        if not any((attr_name.startswith("__"), _is_property(obj, attr_name))):
            yield attr_name, getattr(obj, attr_name)


def _get_module_object_attributes(mod):
    return ((attr_name, getattr(mod, attr_name)) for attr_name in dir(mod))


def get_object_attributes(obj):
    return _get_module_object_attributes(obj) if inspect.ismodule(obj) else _get_class_object_attributes(obj)
