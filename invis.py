"""
invis.py

An invisible framework for enforcing type checking at runtime.

Copyright (c) 2019, Diogo Flores.
License: MIT
"""

from collections import ChainMap
from dataclasses import dataclass
from functools import wraps
from inspect import signature

# Imports the objects defined in the list below when you do:  from invis import *
__all__ = ["NaturalNum", "Invis", "inv"]

_contracts = {}

# The Descriptor Protocol is kind of like @property on steroids.
# For a great discussion on it, see D.Beazley "Python 3 Metaprogramming"
class Descriptor:
    def __init_subclass__(cls):
        _contracts[cls.__name__] = cls

    def __set__(self, instance, value):
        self.check(value)
        instance.__dict__[self.name] = value

    def __set_name__(self, cls, name):
        self.name = name

    @classmethod
    def check(cls, value):
        pass


class Typed(Descriptor):
    type = None
    
    @classmethod
    def check(cls, value):
        if cls.__qualname__ == "Function":
            if value:  # Not None
                if value not in _builtins:
                    assert callable(
                        value
                    ), f"Expected: <class 'function'> got: {type(value)}"
                else:
                    raise TypeError(f"Expected: <class 'function'> got: {value}")
            else:
                # In case you pass an empty builtin e.g. []
                # Or if you pass a zero integer.
                if type(value) in _builtins:
                    raise TypeError(
                        f"Expected: <class 'function'> got: empty {type(value)}"
                    )

        else:
            assert isinstance(
                value, cls.type
            ), f"Expected: {cls.type} got: {type(value)}"
        super().check(value)


# Defining something as a "Function" with type = object, and then checking if the object
# is callable works for both methods and user defined/builtin functions.
class Function(Typed):

    type = object


########################## -- User defined classes/mixins -- ###########################

# Define your own generic classes/mixins with the name/type you wish.
# You will be able to enforce the types defined here in any derived class of
# (Base, Typed) without any additional importing other than: from invis import Invis (or
# any other class that derives from Base, Typed).
# If you require to enforce these types in random functions (methods from derived classes
# are already included) throughout your program, then you must import the classes you are
# defining directly (plus the 'inv' decorator) or you may just: from invis import *
# given that you add the classes to the __all__ list defined at the top of this file.
# A few examples are provided below:


class CMap(Typed):
    from collections import ChainMap

    type = ChainMap


# class NArray(Typed):
#    import numpy
#
#    type = numpy.ndarray


class Positive(Descriptor):
    @classmethod
    def check(cls, value):
        assert value > 0, f"value: {value} must be > 0"
        super().check(value)


class NaturalNum(int, Positive):  # Mixin
    pass


########################################################################################

# There are multiple ways to access the builtins but this seems to be the most explicit.
_builtins = {bytes, bytearray, complex, dict, float, int, list, set, str, tuple}


def inv(func):
    """
    Checks functions + type assertion.
    """
    sig = signature(func)

    ann = dict(func.__annotations__)  # , func.__globals__.get("__annotations__", {}))

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            if name in ann:

                # This if statement accomodates possible user defined Mixins, allowing such
                # to have their first Parent being a builtin and not a class which defines
                # a "type" attribute equal to a builtin.
                if not hasattr(ann[name], "type") and ann[name] not in _builtins:
                    try:
                        ann[name].type = ann[name].__bases__[0]
                    except IndexError:
                        pass  # The class is not a Mixin, yet it is defined in this module.
                    else:
                        assert isinstance(
                            val, ann[name].type
                        ), f"Expected {val} to be of type:{ann[name].type} got:{type(val)}"

                        # Delete the attribute that was just assigned, otherwise type
                        # checking won't be enforced in consequent instances of the class
                        # because the if statement above will be ignored since ann[name]
                        # will now have a type and the following try/except will succeed
                        # because Mixins have a "check" method, yet the first Parent of
                        # the class (which is supposedly a builtin) won't be checked and
                        # hence render the Mixin useless.
                        delattr(ann[name], "type")
                try:
                    ann[name].check(val)
                except AttributeError:  # builtins don't have a .check() attribute
                    assert isinstance(
                        val, ann[name]
                    ), f"Expected {val} to be of type: {ann[name]} but got: {type(val)}"
        return func(*args, **kwargs)

    return wrapper


def _types(cls, name, val):
    if val in _contracts.values():  # classes defined in this module.
        contract = val()
    else:
        # If it is not the above, nor a builtin type, then val must be a user defined
        # object/class in a different file.
        # Make a new class with the name/type of the object provided, initialize it
        # and enforce type checking on this new type.
        contract = type(val.__name__, (Typed,), {"type": val})()

    contract.__set_name__(cls, name)
    return contract


class BaseMeta(type):
    def __prepare__(cls, *args, **kwargs):
        return ChainMap({}, _contracts)

    def __new__(meta, name, bases, clsdict, **kwargs):
        clsdict = clsdict.maps[0]
        if kwargs:  # dataclass params.
            clsdict = {**clsdict, **kwargs}
        return super().__new__(meta, name, bases, clsdict)


_derived_classes = {}


class Base(metaclass=BaseMeta):
    def __init_subclass__(cls):
        if not issubclass(cls, Typed):
            raise Exception("Must inherit from both Base and Typed.")

        # This allows a class to inherit from a subclass of (Base,Typed) without
        # the need to initialize it.
        # This is useful when we are only interested in accessing the
        # parent class methods/variables (which are stored in the cls.__dict__, not on
        # __dataclass_fields__).
        if issubclass(cls, tuple(_derived_classes.values())):
            bases = [*cls.__bases__]
            try:
                for index, _ in enumerate(bases):
                    try:
                        del bases[index].__dataclass_fields__
                    except AttributeError:
                        # Since we are deleting elements, the list decreases in
                        # size by 1 each time, hence the need for "index - 1".
                        del bases[index - 1].__dataclass_fields__

            except AttributeError:
                pass  # Already deleted.

        # dataclass parameters customization.
        if not "params" in cls.__dict__:
            cls = dataclass(cls)
        else:
            assert isinstance(cls.__dict__["params"], dict), "params must be a dict"

            # Default dataclass parameters
            args = dict(
                init=True,
                repr=True,
                eq=True,
                order=False,
                unsafe_hash=False,
                frozen=False,
            )
            for key, value in cls.__dict__["params"].items():
                assert key in args, f"params must be one of: {args.keys()}"
                assert isinstance(value, bool), "value must be a Boolean"
            cls = dataclass(cls, **cls.__dict__["params"])

        # This allows for a subclass of (Base, Typed) to be used as an interface.
        # e.g class MeaningfulName(Base, Typed): pass
        # class ProjectModule(MeaningfulName): ...
        if "__annotations__" in cls.__dict__:
            for name, val in cls.__annotations__.items():
                contract = _types(cls, name, val)
                setattr(cls, name, contract)

        # The reason why this loop is not indented inside the if statement above is
        # that so one can define a class that has no "__annotations__" (as the comment
        # above explains), albeit defines methods which are meant to be used by derived
        # classes, with type checking enforced.
        for name, val in cls.__dict__.items():
            if callable(val):
                setattr(cls, name, inv(val))  # Apply decorator

        @classmethod
        def check(cls, value):
            pass

        cls.check = check

        _derived_classes[cls.__name__] = cls


# This is the class you inherit from when you do: from invis import Invis.
# An alternative approach would be to to define the "Master" classes for your project
# here without any annotations or methods, and then import them directly.
# e.g. from invis import Kls
class Invis(Base, Typed):
    pass
