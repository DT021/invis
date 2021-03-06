[![Build Status](https://travis-ci.org/dxflores/invis.svg?branch=master)](https://travis-ci.org/dxflores/invis)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/2d318652634a424eaddd354be41b114d)](https://www.codacy.com/manual/dxflores/invis?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dxflores/invis&amp;utm_campaign=Badge_Grade)
[![codecov](https://codecov.io/gh/dxflores/invis/branch/master/graph/badge.svg)](https://codecov.io/gh/dxflores/invis)

# Invis

Invis is an invisible framework which purpose is to enforce type checking of both builtins as well as user defined types at **runtime**. 
It is distributed as a single file with no extra dependencies other than the Python Standard Library (>= 3.7).

To install: `pip install invis`

A discussion about the project, held on reddit's algotrading subforum, can be found [here](https://www.reddit.com/r/algotrading/comments/dwrk59/a_micro_framework_to_give_you_peace_of_mind_with/).

A comprehensive tutorial on how to use the framework follows.

## "Hello, World." example
```python
# example1.py

from invis import Invis

class Kls(Invis):
    first: int
    second: bytes
    third: float

k = Kls(3, b"Hi", 5.0)	# OK
k.first = 3.0		# Error, Kls.first only accepts integers
```
*Kls* is a [dataclass](https://docs.python.org/3/library/dataclasses.html) behind the scenes and if we don't initialize it with the annotated types, we will get an error. 
If after initialization we try to change one of the attribute values and we don't pass the expected type, we will also get an error. 

*This is the essence of Invis, to make type checking/enforcing invisible to the end user, yet highly customizable to the library/framework author, as we will see below.*

## The 'Function' keyword
*(This keyword is predefined in Invis's source code and is meant to represent a [callable](https://docs.python.org/3/library/functions.html#callable) in python, in other words, it enforces that the argument passed to it must be callable, much like the keyword 'int' enforces that the argument must be an integer. It is the only keyword added by the framework.)*
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

k2 = Kls(min)	# Passing a builtin function
k2.first(4, 7)	# returns 4
```
Notice that we are initializing both instances of *Kls* with only one argument, since the second one defaults to a lambda.
Given that both attributes are (and must be) callable,  then we can just call them with different values.
We could even initialize Kls with a method from a different class, since *it* is also callable.

*(We will see below, on the "Bonus" part of this tutorial, how we could force "func" to only accept a specific type of argument when we call it.)*

## Customizing Invis 
Until now, all the type checking we did was 'against' builtin types, however every project has different needs and Invis easily adapts to them, with minimal coding from your side. 
To enforce user-defined types, you must create a module named "_invis.py" at the root of your project (think of it as an Header file),  and inside that module define the types that you want to enforce on the classes/functions throughout your project.

(Suggestion: after using Invis in my own projects for a while, I grew fan of naming all my "user-defined-types" classes in all capital letters instead of some alternative to the original name, assuming that the ideal (CamelCase) name is already taken by the object I want to enforce types of.  
e.g. a class that would assert the type to be of pd.DataFrame, I would name it 'DATAFRAME', instead of 'DFrame' or 'DataF'.  
This somehow blends with pep8, which defines that all capital letters should only be used for constants - I think of these classes as "constant-types")

Let's see an example: 
```
. project
	├── package1
	│   	├── module1.py
	│   	└── module2.py
	└── package2
	│   	├── module3.py
	│   	├── module4.py
	│   	└── package3
	│       	└── module5.py
	│── setup.py
	│── README.md
	└── _invis.py			<----- "_invis.py"
```

By adding the following code to "_invis.py"
```python
# _invis.py

import numpy as np
from invis import Typed

__all__ = ['NP_ARRAY']

class NP_ARRAY(Typed):

    type = np.ndarray
```
We can now enforce type checking for "NP_ARRAY" in any module of our project:
```python
#example 3.py

import numpy as np
from invis import Invis

class Kls(Invis):
    first: NP_ARRAY
    
    def func(self, arr: NP_ARRAY):
	    return arr * self.first


arr = np.array([1,2,3])
arr2 = np.array([4,5,6])

k = Kls(arr)	# OK
k.func(arr2)	# returns array([ 4, 10, 18])
```
And unless we initialize *Kls* with a *numpy array* we will get an error. 
The same applies for the method 'func' which only accepts a *numpy array*, otherwise it will throw an error.

### We can expand "_invis.py" to accommodate for techniques such as Mixins 
*By appending the following two classes, 'Positive' and 'NaturalNum'*
```python
# _invis.py 

import numpy as np
from invis import Typed, Descriptor

__all__ = ['NP_ARRAY', 'NATURAL_NUM']

class NP_ARRAY(Typed):

    type = np.ndarray


class POSITIVE(Descriptor):
    @classmethod
    def check(cls, value):
        assert value > 0, f"value: {value} must be > 0"
        super().check(value)


class NATURAL_NUM(int, POSITIVE):  # Mixin - instances must be both integer and >= 1
    pass
```
We can then use *NATURAL_NUM* in our own classes/functions the same way we used *NP_ARRAY*:
```python
# example4.py

from invis import Invis

class Kls(Invis):
    first: NATURAL_NUM

k = kls(0) # Error: must be an integer >= 1
```
*(Notice that we didn't had to import NATURAL_NUM, the same way that we didn't had to import NP_ARRAY , once they are defined in the "_invis.py" module,  then they become available to all classes that derive from Invis)*

### Now let's define two classes in two separate modules
*(And have the second module only accept objects that are of the type defined in the first module.)*
```python
# example5.py | module1.py

from dataclasses import field # To use the field keyword, we must import it.
from invis import Invis

class Person(Invis):
    name: str
    age: int
    info: dict = field(default_factory=dict, repr=False)

ed = Person(name="Edward", age=36)
jul = Person(name="Julian", age=48, info={'Australian': True})
```
```python
# example5.py | module2.py

from invis import Invis
from package1.module1 import Person, ed, jul

class Kls(Invis):
    first: Person

    def func(self, num: NATURAL_NUM = 10):
        return self.first.age + num

k = Kls(ed) 
k.func()   	# Returns 46

k.first = 10    # Error, first only accepts Person objects
k.first = jul   # OK, because jul is also a Person object
k.func(10.5)    # Error, float was passed, only NATURAL_NUM (int >= 1) allowed
k.func(10)      # OK, returns 58
```
Pretty cool, right? Invisible type checking of user defined classes, in different modules, at runtime, without the need to write any extra code other than the import statement. Try it in a REPL.

*Note that we didn't add the type "Person" to "_invis.py", hence it must be imported from the module where it is defined to the module where we want to use/enforce it. 
Additionally, even if Person is considered a "user-defined-type" by the framework, because we are explicitly importing it at the top of the module, it's clear that the class is defined somewhere other than in _invis.py, which by itself doesn't require explicit imports of the classes defined within, and so there's no need for the all capital naming (e.g. PERSON) suggestion given before in this tutorial.*

### Inheritance without initialization

*(The following example shows another feature of Invis, which is the ability to inherit from other Invis classes without having to initialize its attributes, yet still have access to all the methods, as well as class variables defined in the inheritance chain)*

```python
# example6.py

from dataclasses import field
from invis import Invis

class Original(Invis):	# Defining Original as an interface
    pass

class Kls_1(Original):
    first: float
    second: set = field(default_factory=set)
    ClassVar = "Hi"

    def func1(self):
        return "func1"

class Kls_2(Kls_1):
    first: NP_ARRAY
    second: float

    def func2(self):
        return self.first * self.second
    
    def func3(self, arg: int):
        return arg + 10

class Kls_3(Kls_2):
    first: int


k = Kls_3(2)    # Don't have to initialise any of the parent classes

# Yet, we still have access to the methods + class variables defined up the chain.
k.ClassVar      # Returns "Hi"
k.func1()       # Returns "func1"
k.func3(10)     # Returns 20
```

## Bonus
*To enforce types in  random functions (those outside of a class that inherits from Invis), we can import a decorator 'inv'.*
```python
# example7.py

from invis import inv

@inv
def func(a:int, b: float):
    return a + b

func(2, 3.0)
```
Albeit, the above example only works for checking 'against' builtin types, to enforce type checking of user defined types (those that we previously defined in "_invis.py") we must import them explicitly, as shown below:
```python
# example 8.py

import numpy as np
from invis import inv, Function, NATURAL_NUM, NP_ARRAY 

@inv
def func(a:Function, b:NP_ARRAY, c: NATURAL_NUM):
    return a(b * c)

array = np.array([1,2,3])
func(max, array, 2)     # Returns 6
```

**To customize the dataclass parameters**

```python
# example9.py

from invis import Invis

class Kls(Invis, params=dict(repr=False)): # We must pass a dictionary named "params"
	first: int

k = Kls(5) # No repr
```
You can find all available parameters and their functionality in the official [dataclasses](https://docs.python.org/3/library/dataclasses.html) documentation.
