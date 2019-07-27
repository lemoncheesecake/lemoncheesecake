.. _`matchers`:

Matchers
========

Lemoncheesecake comes with support of matchers, a feature inspired by
`Hamcrest <http://hamcrest.org/>`_ / `PyHamcrest <https://github.com/hamcrest/PyHamcrest>`_.

The following stock matchers are available:

- Values:

  - ``equal_to(expected)``: check if actual ``==`` expected

  - ``not_equal_to(expected)``: check if actual ``!=`` expected

  - ``greater_than(expected)``: check if actual ``>`` expected

  - ``greater_than_or_equal_to(expected)``: check if actual ``>=`` expected

  - ``less_than(expected)``: check if actual ``<`` expected

  - ``less_than_or_equal_to(expected)``: check if actual ``<=`` expected

  - ``is_between(min, max)``: check if actual is between min and max

  - ``is_none()``: check if actual ``== None``

  - ``is_not_none()``: check if actual ``!= None``

  - ``has_length(expected)``: check if value has expected length (``expected`` can be a value or a ``Matcher`` object)

  - ``is_true()``: check if value is a boolean true

  - ``is_false()``: check if value is a boolean false

  - ``is_json(expected)``: check is the actual JSON equals ``expected``, if not, the unified diff of
    actual vs expected is displayed

- Character strings:

  - ``starts_with(expected)``: check if the actual string starts with ``expected``

  - ``ends_with(expected)``: check if the actual string ends with ``expected``

  - ``match_pattern(expected)``: check if the actual string match ``expected`` regexp (expected can be a raw string or an object
    returned by ``re.compile()``)

  - ``is_text(expected)``: check is the actual (multi-lined) text equals ``expected``, if not, the unified diff of
    actual vs expected is displayed


- Types (``expected`` is optional and can be a value or a matcher object):

  - ``is_integer([expected])``: check if actual is of type ``int``

  - ``is_float([expected])``: check if actual is of type ``float``

  - ``is_str([expected])``: check if actual is of type ``str`` (or ``unicode`` if Python 2.7)

  - ``is_dict([expected])``: check if actual is of type ``dict``

  - ``is_list([expected])``: check if actual is of type ``list`` or ``tuple``

  - ``is_bool([expected])``: check if actual is of type ``bool``

- Iterable:

  - ``has_item(expected)``: check if the actual iterable has an item that matches expected (expected can be a value
    or a Matcher)

  - ``has_items(expected)``: check if the actual iterable contains **at least** the expected items

  - ``has_only_items(expected)``: check if the actual iterable **only contains** the expected items

  - ``is_in(expected)``: check if actual is **among** the expected items

- Dict:

  - ``has_entry(expected_key [,expected_value])``: check if actual dict has ``expected_key`` and (optionally) the
    expected associated value ``expected_value`` (which can be a value or a matcher)

- Logical:

  - ``is_(expected)``: return the matcher if ``expected`` is a matcher, otherwise wraps ``expected`` in the
    ``equal_to`` matcher

  - ``is_not(expected)``: make the negation of the ``expected`` matcher (or ``equal_to`` if the argument is
    not a matcher)

  - ``all_of(matcher1, [matcher2, [...]])``: check if all the matchers succeed (logical **AND** between all the
    matchers)

  - ``any_of(matcher1, [matcher2, [...]])``: check if any of the matchers succeed (logical **OR** between all the
    matchers)

  - ``anything()``, ``something()``, ``existing()``: these matchers always succeed whatever the actual value is (only
    the matcher description changes to fit the matcher's name)


Those matcher are used by a matching function:

- ``check_that(hint, actual, matcher, quiet=False)``: run the matcher, log the result and return the matching result
  as a boolean

- ``require_that(hint, actual, matcher, quiet=False)``: run the matcher, log the result and raise an ``AbortTest``
  exception in case of a match failure

- ``assert_that(hint, actual, matcher, quiet=False)``: run the match, in case of a match failure (and only in this case)
  log the result and raise an ``AbortTest`` exception

The ``quiet`` flag can be set to ``True`` to hide the matching result details in the report.

The ``lemoncheesecake.matching`` module also provides helper functions to ease operations on dict object:

The code:

.. code-block:: python

    data = {"foo": 1, "bar": 2}
    check_that("data", data, has_entry("foo", equal_to(1)))
    check_that("data", data, has_entry("bar", equal_to(2)))

Can be shortened like this:

.. code-block:: python

    check_that_in(
        {"foo": 1, "bar": 2},
        "foo", equal_to(1),
        "bar", equal_to(2)
    )

The same dict helper counter parts are available for:

- ``require_that`` => ``require_that_in``

- ``assert_that`` => ``assert_that_in``

If one match fails in a test, this test will be marked as failed.
