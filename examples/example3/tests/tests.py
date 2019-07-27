import json

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

SUITE = {"description": "My test"}


@lcc.test("test")
def test():
    check_that("val1", 1, equal_to(1))
    check_that("val1", 1, equal_to(2))
    check_that("val", 2, all_of(greater_than(1), greater_than(4)))
    check_that("dict", {"foo": "bar"}, has_entry("foo", equal_to("bar")))
    check_that("dict", {"fooo": "bar"}, has_entry("foo", equal_to("bar")))
    check_that("dict", {"foo": "baz"}, has_entry("foo", equal_to("bar")))

    check_that_in({"foo": 3}, "foo", greater_than(2))

    check_that("val", "foo", is_integer())

    check_that("float value", 2.5, all_of(is_float(), greater_than(2)))

    check_that("float value", 2.5, is_float(greater_than(2)), quiet=True)

    check_that("value", "42", match_pattern("^\d+$"))

    check_that("value", "42", match_pattern("^\d+$", "a number"))

    check_that("value", "42", match_pattern("^\d+$", "a number", mention_regexp=True))

    check_that("list", (1, 2, 3, 4), has_item(3))

    check_that("value", 1, is_integer(greater_than(0)))

    check_that("value", 1, is_integer(not_(equal_to(0))))

    check_that("list", [3, 1, 2], has_items([1, 2 , 3, 4]))

    check_that("list", [3, 1, 2], has_only_items([1, 2]))

    check_that("list", [3, 1, 2], has_length(equal_to(3)))

    check_that("val", 1, is_in([1, 2, 3]))

    check_that("val", 2, is_between(1, 3))

    # check_that_entry(["foo", "bar"], {"foo": {"bar": 2}}, greater_than(1))

    check_that("dict", {"foo": {"bar": 2}}, has_entry(["foo", "bar"], greater_than(1)))

    d = {
        "foo": 1,
        "bar": 2,
        "baz": {
            "toto": 21,
            "titi": 42
        }
    }

    lcc.log_info(json.dumps(d, indent=4))

    check_that("dict", d, has_entry("foo", equal_to(1)))

    check_that("dict", d, all_of(
        has_entry("foo", equal_to(1)),
        has_entry("bar", is_between(1, 3)),
        has_entry("baz", all_of(
            has_entry("toto", is_(21)),
            has_entry("titi", is_(42))
        ))
    ))

    check_that("value", 2, any_of(1, 2, 3))

    lst = [{"foo": 1, "bar": 2}]

    check_that("list", lst, has_item(all_of(
        has_entry("foo", is_(1)),
        has_entry("bar", is_(2))
    )))

    lcc.set_step("is_text")
    check_that(
        "text",
        "\n".join("line%d" % (nb+1) for nb in range(10)),
        is_text("\n".join("line%d" % (nb+1) for nb in range(10)))
    )
    check_that(
        "text",
        "\n".join("line%d" % (nb+1) for nb in range(10)),
        is_text("\n".join("line%d" % (nb+1) for nb in range(12)))
    )

    lcc.set_step("is_json")
    check_that(
        "json",
        {"foo": 1, "bar": 2},
        is_json({"foo": 1, "bar": 2})
    )
    check_that(
        "json",
        {"foo": 1, "bar": 2, "baz": 3},
        is_json({"foo": 1, "bar": 2})
    )
    check_that(
        "dict",
        {
            "some": "thing",
            "data": {"foo": 1, "bar": 2, "baz": 3}
        },
        all_of(
            has_entry("some", equal_to("thing")),
            has_entry("data", is_json({"foo": 1, "bar": 2}))
        )
    )
