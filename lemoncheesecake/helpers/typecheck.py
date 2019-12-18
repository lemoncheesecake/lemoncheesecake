import six


def check_type(value_description, value, type_description, check, optional=False, show_actual_type=True):
    if optional and value is None:
        return

    if not check(value):
        error = "expect %s for %s" % (type_description, value_description)
        if show_actual_type:
            error += ", got %s" % value.__class__.__name__
        raise TypeError(error)


def check_type_string(value_description, value, optional=False):
    return check_type(
        value_description, value, "string", lambda value: isinstance(value, six.string_types), optional=optional
    )


def check_type_bool(value_description, value):
    return check_type(
        value_description, value, "boolean", lambda value: type(value) is bool
    )


def check_type_dict(value_description, value):
    return check_type(
        value_description, value, "dict", lambda value: isinstance(value, dict)
    )
