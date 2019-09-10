import six


def check_type(name, value, type_description, check, optional=False):
    if optional and value is None:
        return

    if not check(value):
        raise TypeError("expect %s for '%s', got %s" % (type_description, name, value.__class__.__name__))


def check_type_string(name, value, optional=False):
    return check_type(
        name, value, "string", lambda value: isinstance(value, six.string_types), optional=optional
    )


def check_type_bool(name, value):
    return check_type(
        name, value, "boolean", lambda value: type(value) is bool
    )