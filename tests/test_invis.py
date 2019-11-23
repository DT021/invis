import pytest
from invis import Invis

"""
Since Invis purpose is to assert types, it's a bit contrived to write assertion tests,
nevertheless the following covers ~97% of the builtins + the Function keyword.
(The only types that Invis accepts if you dont add a "_invis.py")

Additionally, there is some commented code that was used to test some of the examples
from the README.md.
Such can be used by each user as a starting point to write its own tests for its own
defined types.
"""

################################# -- Builtins-- ######################################


def test_permutations_builtins():

    # builtins = {bytes, bytearray, complex, dict, float, int, list, set, str, tuple}
    values = [b"hello", bytearray(1), 1 + 1j, {}, 1.0, 2, [], "hi", ()]

    for val in values:

        class Test(Invis):
            first: type(val)

        # iterate through all values in the list again and if the value is different
        # than the current attribute type of the class Test, assume it will raise an
        # error. If it is equal, assume it will not.
        for elem in values:
            if type(elem) != type(val):
                with pytest.raises(AssertionError):
                    Test(elem)  # Raises an error. Initialized with a different type.
            else:
                Test(
                    elem
                )  # Does not raise an error. Same type as Test.first attribute.


############################## -- Function Keyword -- ################################


def func(a, b):
    return a + b


# A non exhaustive list of values to test on the following test function.
# The reason there is both e.g. [] and list, is to be able to test trying to
# initialize the 'Function' with both.
# Both should fail, even if the latter is callable.
values = [
    "hello",
    [],
    {},
    (),
    1,
    0,
    4.0,
    -5,
    func,  # The function we defined above
    bytes,
    bytearray,
    complex,
    dict,
    float,
    int,
    list,
    set,
    str,
    tuple,
]

_builtins = {bytes, bytearray, complex, dict, float, int, list, set, str, tuple}


def test_Function():
    class Test(Invis):
        first: Function

    for val in values:
        if callable(val):
            if val not in _builtins:
                Test(val)
            else:
                with pytest.raises(TypeError):
                    Test(val)
        else:
            with pytest.raises((AssertionError, TypeError)):
                Test(val)


"""
# The classes (test_CMAP and test_NATURAL_NUM) found at the end of this file,
# serve as an example/starting point for you to implement your own tests of your own defined types.
# The following code must be defined in a module called _invis.py

# _invis.py

from collections import ChainMap
from invis import Invis, Typed, Descriptor

__all__ = ['CMAP', 'NATURAL_NUM']

class CMAP(Typed):

    type = ChainMap

class POSITIVE(Descriptor):
    @classmethod
    def check(cls, value):
        assert value > 0, f"value: {value} must be > 0"
        super().check(value)


class NATURAL_NUM(int, POSITIVE):  # Mixin - instances must be both integer and >= 1
    pass

"""
"""
def test_CMAP():
    class Test(Invis):
        first: CMAP

    for val in values:
        if not hasattr(val, "type"):
            if type(val) != Test.first.type:
                with pytest.raises(AssertionError):
                    Test(val)
            else:
                Test(val)
        else:
            if val.type != Test.firs.type:
                with pytest.raises(AssertionError):
                    Test(val)
            else:
                Test(val)


def test_NATURAL_NUM():
    class Test(Invis):
        first: NATURAL_NUM

    for val in values:
        if type(val) == int:
            if val <= 0:
                with pytest.raises(AssertionError):
                    Test(val)
            else:
                Test(val)
        else:
            with pytest.raises((AssertionError, TypeError)):
                Test(val)
"""
