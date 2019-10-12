from invis import Invis
import pytest

"""
Since Invis purpose is to assert types, it's a bit contrived to write assertion tests,
nevertheless the following covers 100% of the builtins (The only types that Invis 
accepts if you dont add a "_userinvis.py")

Additionally, there is some commented code that was used to test some of the examples 
from the README.md, which can be used by each user as a starting point to write its 
own tests for its own defined types.
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


"""              
########################## -- User defined classes/mixins -- ###########################
from collections import ChainMap
from invis import Invis, Function, NaturalNum, CMap
import pytest

# It is easier to test user defined classes in simple functions, other than one single
# function that must care about each edge case.

_builtins = {bytes, bytearray, complex, dict, float, int, list, set, str, tuple}


def funk(a, b):
    return a + b


# A non exhaustive list of values to test on the following test functions.
# The reason there is both e.g. [] and list, is to be able to test intializing the
# 'Function' type with an empty [] as well as list. Both should fail, even if the latter
# is callable.
values = [
    ChainMap,
    [],
    {},
    (),
    1,
    0,
    -5,
    dict,
    "hello",
    tuple,
    list,
    funk,
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


def test_CMap():
    class Test(Invis):
        first: CMap

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


def test_NaturalNum():
    class Test(Invis):
        first: NaturalNum

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
