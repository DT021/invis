# Invis
Invis is an invisible framework that enforces runtime checking of both builtins as well as user defined types.
It is distributed as a single file with no extra dependencies other than the Python Standard Library (>= 3.7).

Invis is lean (the source code is ~200LOC) and it's meant to be used as a building block for your project specific needs, nevertheless as is it already provides type check/enforcing for all python builtin types (list, dict, float, ...) on both user defined classes and functions, as well as a few other features, all of which are described below.

I like to think that Invis encapsulates the "Explicit is better than implicit" ideology of Python, by treating type annotations as explicit rather than implicit, and doing it so in a way that keeps the code beautiful and clutter free.

#### Installation:
`python -m pip install git+https://github.com/dxflores/invis.git`


*The following documentation will be presented in a tutorial style and it will show you all you need to know to start using Invis in your projects.*

## Basic example using Python builtins:
```python
# example1.py
from invis import Invis

class Kls(Invis):
    first: int
    second: bytes
    third: float

    def func(self, di: dict, st: str = None):
        if st:
            return st
        return di

k = Kls(3, b"Hi", 5.0)
k.func({}, st = "you")	# Returns "you"
```
*Kls* is a [dataclass](https://docs.python.org/3/library/dataclasses.html) behind the scenes, and if you don't initialize it with the annotated types, it will give you an error. The same applies for the method within, you must call it with a dict as the first argument, and a string as the second argument, otherwise you will get an error.
If after initialization you try to change one of the attribute values and you don't pass the same type as annotated it will also give you an error. 

*This is the essence of Invis, to make type checking/enforcing invisible to the end user, yet highly customizable to the library/framework author, as we will see below.*

## The 'Function' keyword:
 *(this keyword is predefined in Invis's source code and is meant to represent a [callable](https://docs.python.org/3/library/functions.html#callable) in python, in other words it enforces that the argument passed to it must be *callable*, much like the keyword *int* enforces that the argument passed to it must be an integer)*
```python
# example2.py
from invis import Invis

def func(x, y):
    return x + y
    
class Kls(Invis):
    first: Function
    second: Function = lambda z: z ** 2

k = Kls(func)	# Passing the function defined above to the first attribute
k.first(2, 3) 	# returns 5
k.second(3)  	# returns 9
```
Notice that we are initializing *Kls* with only one argument, func, since the second one defaults to a lambda.
Since both attributes are (and must be) callable,  then we can just call them. 
*(We will see below on the *"Bonus"* part of this tutorial how we could force *func* to only accept a specific type of argument when we call it.)*


#### Expanding on the previous example, we could initialize  *Kls* with a builtin function instead of a user defined one:
```python
# example2.py continuation.

# with min
k = Kls(min)
k.first(4,7)   # returns 4

#or with len.
k = Kls(len)
k.first([1, {}, "hello", 0.1, ()]) # returns 5
```
*You could even pass a method from a different class. Anything that is a callable will work. Anything that is not will fail with an error.*

## Customizing Invis: 
Until now, all the type checking we did was with the builtin types, however every project has different needs and I wrote invis to be as adaptable as possible to those, with minimal coding from your side. 

e.g. you could add the following lines to Invis's source code (the right place to do it is annotated in the code)
```python
# invis.py

class NArray(Typed):
    import numpy as np

    type = np.ndarray
```
And if you did so, then you could define the class below:
```python
#example 3.py
from invis import Invis

class Kls(Invis):
    first: NArray
    second: int

    def func(self, arr: NArray):
	    return arr * self.second
```
And as you probably guessed, unless you pass a *Numpy array* as the first argument and an *int* as the second you will get an error. 
The same applies for the method within *Kls*, which takes a single argument,  a *Numpy array*.

###  The idea of editing Invis's source code can be expanded further to accommodate for techniques such as Mixins: 
*(By adding the following two classes to invis's source code)*
```python
# invis.py 

class Positive(Descriptor):
    @classmethod
    def check(cls, value):
        assert value > 0, f"value: {value} must be > 0"
        super().check(value)


class NaturalNum(int, Positive):  # Mixin
    pass
```
You can then use *NaturalNum* in your own classes the same way you used *NArray*:
```python
# example4.py
from invis import Invis

class Kls(Invis):
    first: NaturalNum

k = kls(1) # first needs to be both an int as well as positive (>= 1)
```
*(Notice that you didn't had to import **NaturalNum**, the same way that you didn't had to import **NArray** , once you defined it in the source code then it becomes available to all classes that derive from Invis)*

### Now let's define two classes on two separate files:

```python
# example5.py
# fileA.py
from invis import Invis
from dataclasses import field # To use the field keyword, we must import it.

class Person(Invis):
    name: str
    age: int
    info: dict = field(default_factory=dict, repr=False)

c = Person(name="Camilla", age=27)
d = Person(name="Diogo", age=28, info={'has_dog': True})
```
```python
# example5.py
# fileB.py
from invis import Invis
from fileA import Person, c, d

class Kls(Invis):
    first: Person

    def func(self, num: NaturalNum = 10):
        return self.first.age + num

k = Kls(c) 	# first is a Person object
k.func()   	# Returns 37

k.first = 10    # Error, first only accepts Person objects
k.first = d     # OK, because d is also a Person object
k.func(10.5)    # Error, float was passed, only NaturalNum allowed
k.funk(10)      # OK, returns 38
```
Pretty cool, right? Invisible type checking of user defined classes at runtime.

### Inheritance without initialization:

*(The following example shows another feature of Invis, which is the ability to inherit from other Invis classes without having to initialize its attributes, yet still have access to all the methods, as well as class variables defined in the inheritance chain)*

```python
# example6.py
from invis import Invis
from dataclasses import field

class Original(Invis):	# Defining Original as an interface
    pass

class Kls_1(Original):
    first: float
    second: set = field(default_factory=set)
    ClassVar = "Hi"

    def func1(self):
        return "func1"

class Kls_2(Kls_1):
    first: NArray
    second: float

    def func2(self):
        return self.first * self.second
    
    def func3(self, arg: int):
        return arg + 10

class Kls_3(Kls_2):
    first: int


k = Kls_3(2)    # Didn't had to initialize the other classes.

# Yet, it can still access the methods + class variables defined up the chain:
k.ClassVar      # Returns "Hi"
k.func1()       # Returns "func1"
k.func3(10)     # Returns 20
```

## Bonus:
*If you need type checking on a random function (outside of a class that inherits from *Invis*), you can import a decorator which will give you the same type checking/enforcing for both builtin and user defined types/classes.*
```python
# example7.py
from invis import inv

@inv
def func(a:int, b: float):
    return a + b

func(2, 3.0)
```
The above example only works for builtin types, to enforce type checking of user defined types you can either import them explicitly or add the desired classes to __ all__, in the source code, and then "from invis import *"

```python
# example 8.py
from invis import inv, Function, NaturalNum, NArray # Equal to: from invis import *  
import numpy as np

@inv
def func(a:Function, b:NArray, c: NaturalNum):
    return a(b*c)

array = np.array([1,2,3])
func(max, array, 2)     # Returns 6
```

#### If you need to customize the dataclass parameters, you can do it like this:

```python
from invis import Invis

class Kls(Invis, params=dict(repr=False)): # You must pass a dictionary named "params"
	first: int

k = Kls(5) # No repr
```
*You can find all available parameters and their functionality in the official [dataclasses](https://docs.python.org/3/library/dataclasses.html) documentation.*

#### End of tutorial.
___

## Contributing:

Both bug reports and pull/feature requests are welcomed, and the latter will be considered, nevertheless I would like to be explicit on my vision for this project.
I want to keep *Invis* as lean as possible so every unique user will be able to hack it, if they deem necessary, to fit their project needs without having to read through endless lines of code.
Given the above and the fact that the source code is thoroughly commented, it might seem almost enticing to start adding features, but I will defer those unless they prove to be for the "greater good" and not project specific.
I would suggest, however, is that you submit any cool ideas/features/approaches of how you use Invis in your project to the /examples page so everyone can drive inspiration from them.

## Acknowledgments:

 - This project was inspired by, and builds upon, the ideas presented by David Beazley @dabeaz in his fantastic talk 
 [The Fun of Reinvention](https://www.youtube.com/watch?v=5nXmq1PsoJ0&t).
 - Also essential to this project was the work done by Eric Smith @ericvsmith, author of dataclasses, which lay the foundation for Invis.
- I have used [Black](https://github.com/psf/black), by Łukasz Langa @ambv, which turned out to be a proper partner in crime. 
 
- One last acknowledgment for the Python core-developers, and all others, who keep making Python a better programming language, version after version.
