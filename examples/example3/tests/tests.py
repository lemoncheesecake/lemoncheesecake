import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

TESTSUITE = {"description": "My test"}

@lcc.test("test")
def test():
    check_that("val1", 1, equal_to(1))
    check_that("val1", 1, equal_to(2))
    check_that("val", 2, all_of(greater_than(1), greater_than(4)))
    check_that("dict", {"foo": "bar"}, has_entry("foo", equal_to("bar")))
    check_that("dict", {"fooo": "bar"}, has_entry("foo", equal_to("bar")))
    check_that("dict", {"foo": "baz"}, has_entry("foo", equal_to("bar")))
 
    check_that_entry("foo", {"foo": 3}, greater_than(2))
 
    check_that("val", "foo", is_integer())
     
    check_that("float value", 2.5, all_of(is_float(), greater_than(2)))
 
    check_that("float value", 2.5, is_float(greater_than(2)), quiet=True)

    check_that("value", "42", match_pattern("^\d+$"))
    
    check_that("list", (1, 2, 3, 4), has_item(3))

    check_that("value", 1, is_integer(greater_than(0)))
    
    check_that("value", 1, is_integer(is_not(equal_to(0))))
    
    check_that("list", [3, 1, 2], has_values([1, 2 ,3, 4]))

    check_that("list", [3, 1, 2], has_only_values([1, 2]))

    # Expect value to be integer and to be greater than 0
    
    # Expect value to be an integer that is greater than 0

    # Expect dict to have entry 'value' that is an integer that is greater than 0
    
    # Expect dict to have entry 'value' that is a string that starts with 'foo'

