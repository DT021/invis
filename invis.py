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
import os
from pathlib import Path
import sys

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


# There are multiple ways to access the builtins but this seems to be the most explicit.
_builtins = (bytes, bytearray, complex, dict, float, int, list, set, str, tuple)


class Typed(Descriptor):
    type = None

    @classmethod
    def check(cls, value):
        ERROR = "Expected: <class 'function'> but got"

        if cls.__qualname__ == "Function":
            if value:  # Not None
                if value not in _builtins:
                    if not callable(value):
                        raise AssertionError(f"{ERROR}: {type(value)}")
                else:
                    raise TypeError(f"{ERROR}: {value}")
            else:
                # In case of an empty builtin e.g. []
                if isinstance(value, _builtins):
                    raise TypeError(f"{ERROR} empty: {type(value)}")
        else:
            # To accomodate for e.g. attrib_name: user_type = None
            if type(value) == type(None):
                pass
            elif not isinstance(value, cls.type):
                raise AssertionError(f"Expected: {cls.type} got: {type(value)}")
        super().check(value)


# Defining something as a "Function" with type = object, and then checking if the object
# is callable works for both methods and user defined/builtin functions.
class Function(Typed):

    type = object


# The following try/except looks for a file ("_invis.py") up to two directories from
# the current location where you are trying to execute code. If it finds the file, then
# it will enforce the types defined in the file, otherwise Invis will only enforce
# builtin types.
try:
    current = os.getcwd()
    if os.path.exists(f"{current}/_invis.py"):
        from _invis import *

    else:
        oneup = Path(current).parents[0]
        if os.path.exists(f"{oneup}/_invis.py"):
            sys.path.insert(0, "..")
            from _invis import *
        else:
            twoup = oneup.parents[0]
            if os.path.exists(f"{twoup}/_invis.py"):
                sys.path.insert(1, f"{twoup}")
                from _invis import *
except ImportError:
    pass


def inv(func):
    """
    Checks function signatures + type assertion.
    """
    sig = signature(func)

    ann = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            if name in ann:

                # This if statement accomodates possible user defined Mixins, allowing such
                # to have their first Parent being a builtin.
                if not hasattr(ann[name], "type") and ann[name] not in _builtins:
                    try:
                        ann[name].type = ann[name].__bases__[0]
                    except IndexError:
                        pass  # The class is not a Mixin, yet it's defined in _invis.py
                    else:
                        if not isinstance(val, ann[name].type):
                            raise AssertionError(
                                f"""Expected {val} to be of type:{ann[name].type} but
                                got: {type(val)}"""
                            )
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
                    if not isinstance(val, ann[name]):
                        raise AssertionError(
                            f"Expected {val} to be of type: {ann[name]} but got: {type(val)}"
                        )
            else:
                continue
        return func(*args, **kwargs)

    return wrapper


def _types(cls, name, val):
    # classes defined in '_invis.py' or defined for the first time in a different module
    if val in _contracts.values():
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
        if "params" not in cls.__dict__:
            cls = dataclass(cls)
        else:
            if not isinstance(cls.__dict__["params"], dict):
                raise AssertionError("params must be a dict")

            # Default dataclass parameters
            args = {
                "init": True,
                "repr": True,
                "eq": True,
                "order": False,
                "unsafe_hash": False,
                "frozen": False,
            }

            for key, value in cls.__dict__["params"].items():
                if key not in args or not isinstance(value, bool):
                    raise AssertionError(
                        f"params must be one of: {args.keys()}, and {value} must be a Boolean"
                    )
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


class Invis(Base, Typed):
    """
    This is the (empty) class you import when you do: from invis import Invis.
    """

    pass
