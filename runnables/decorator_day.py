
# Decorator Day
# =============
# 
# An exploration of decorators, closures and functions in general.

# Before I start, this isn't meant as an indepth exploration or explaination of decorators or closures. Some things I breeze over and some things I explain in a little more detail. I'm making an dangerous assumption that you have at least a basic grasp of Python and how it treats functions.
# 
# First Class Functions
# ---------------------
# 
# In Python, functions are first class citizens. What this means is that you can:
# 
# * Pass a function as an argument to another function
# * Return a function from another function
# * Assign a function to a variable
# * Store a function in a data structure

# In[1]:

map(int, ['1', '2','3']) # pass a function as an arguement to another function

def returns_map():
    '''Return a function as a result from a function'''
    return map

my_map = map # assign a function to a variable

my_funcs = [map, list, dict] # store functions in a data structure


# That's great. But what does it have to do with decorators? Everything. Decorators are possible because of this. Wait...what's a decorator?
# 
# Simply put, a decorator is a function that accepts another function an argument and then does something with and then returns the function (and only the function) as it's output. Decorators can modify the function as part as it's processing.

# In[2]:

def my_deco(f):
    print("Decorating {!r}".format(f))
    return f

def do_stuff(*args):
    for a in args:
        print(a)

do_stuff = my_deco(do_stuff)

# alternatively we have a shortcut in @ for decorators.
# this is the same as: other_stuff = my_deco(other_stuff)
@my_deco
def other_stuff():
    print("I feel pretty.")

do_stuff(*range(1,4))
other_stuff()


# Out[2]:

#     Decorating <function do_stuff at 0x7fa8a4079b70>
#     Decorating <function other_stuff at 0x7fa8a4079ae8>
#     1
#     2
#     3
#     I feel pretty.
# 

# But to really talk about decorators, first we have to talk about closures. What's a closure? Simply put, it's a function inside of a function. It's actually little more complicated than that -- things like perserving state come into play -- but for these purposes, it's a function that's *closed over* by another function. Decorators *close over* other functions, decorators *create* closures.

# In[3]:

def closure():
    print("Generating inner")
    def inner():
        return 4 # chosen by fair dice roll
    return inner

closed = closure() # closed is actually now inner and is callable
print(closed())


# Out[3]:

#     Generating inner
#     4
# 

# Something else I should talk about: variable scoping. I won't go into too great of detail and I'll assume you understand the basics of variable scoping in Python, e.g. globals, variable creating inside a scope aren't accessible to things outside of it without black magic.
# 
# Closures create their own scopes. Per the example above, `inner` has access to `closure`'s scope since it's part of `closure`'s scope. However, `inner` can't make meaningful changes to `closure`'s scope unless we key the variable to the `nonlocal` scope. If we don't, we get a `UnboundLocalError: local variable 'name' referenced before assignment` and a nice little traceback. Essentially, closured functions have *read only* access to outer scope variables unless Python's told otherwise.

# In[4]:

def closure(var):
    def inner():
        return var
    return inner

print(closure('a variable')())
# closures return callables, 
# so closure()() is the same as:
# >>> f = closure()
# >>> f()

def hello(name):
    '''Creates a function that says hello to a specific person.'''
    def inner():
        '''Says hello to a specific person.'''
        nonlocal name
        name = 'Hello, {}'.format(name)
        return name
    return inner


print(hello('Fred')())


# Out[4]:

#     a variable
#     Hello, Fred
# 

# This scoping is important because decorators take functions as their arguments. When the decorated function is called with arguments, those arguments become part of the decorator's scope.
# 
# Preserving function metadata
# ----------------------------
# 
# One last thing. When you decorate a function, and the decorator passes it to a closure and the closure calls the decorated function rather than pass it through, you lose all the metadata about the original function.

# In[5]:

def __naive_deco(f):
    def wrapper(*args, **kw):
        print("Doing stuff before allowing {} to run.".format(f.__name__))
        return f(*args, **kw)
    return wrapper

@__naive_deco
def thing(*args, **kw):
    '''Do stuff then return a flux capacitor'''
    return "Capacitor(type='flux')"

print(thing.__name__, thing.__doc__, thing.__dict__)
print(thing())
print(thing(*range(1,4), **{'mcfly':'marty', 'brown':'emmett'}))


# Out[5]:

#     wrapper None {}
#     Doing stuff before allowing thing to run.
#     Capacitor(type='flux')
#     Doing stuff before allowing thing to run.
#     Capacitor(type='flux')
# 

# This can lead to all sorts of issues and problems. Helpful docstrings disappear (and with them any doc tests). `f.__name__ ` returns `wrapper` instead of the proper information. Even more, potentially, troublesome, the function's dictionary disappears, too.  Note that this only happens because we're directly intercepting the call to `thing` -- see how the notice about doing stuff runs each time; however, if we're simply passing f through wrapper, this doesn't happen.
# 
# We could manage this ourselves by creating a decorator decorator.

# In[6]:

def decorator_decorator(deco):
    def wrapper(f):
        g = deco(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    wrapper.__name__ = deco.__name__
    wrapper.__doc__ = deco.__doc__
    wrapper.__dict__.update(deco.__dict__)
    return wrapper

@decorator_decorator
def loggit(f):
    '''Logs a function to stdout'''
    def logger(*args, **kw):
        '''Actually does the logging.'''
        print("Calling {}.".format(f.__name__))
        return f(*args, **kw)
    return logger

@loggit
def double(x):
    '''Doubles a number.'''
    return 2*x


assert(loggit.__name__ == 'loggit')
assert(double.__name__ == 'double')
assert(double.__doc__ == 'Doubles a number.')
print(double(4))


# Out[6]:

#     Calling double.
#     8
# 

# But that's a lot of work just to get decorators to play nice and not (unintentionally) garble data along the way. You might ask, "Why doesn't Python manage this on it's own?" The answers to that are: It's complicated. and It does.
# 
# It's complicated because how does Python know what to pass along when you do something like `list(map(int, ['1','2']))`? It's ambiguous. Should you get the metadata for the original `list`, the `int` function, the `map` function or the outer `list` function? I'm not sure, either.
# 
# It does handle this, however, when explictly instructed to with `functools.wraps`. `wraps` updates the wrapping function to include the correct metadata: function name, docstring, annotations, module origin. And, if needed, it also includes a shortcut to the original wrapped function as well through the `__wrapped__` attribute -- though, keep in that `f.__wrapped__ is f` will return False.

# In[7]:

from functools import wraps

def loggit(f):
    '''Logs a function to stdout'''
    @wraps(f)
    def logger(*args, **kw):
        print('Calling {}'.format(f.__name__))
        return f(*args, **kw)
    return logger

@loggit
def double(x):
    '''Doubles a number.'''
    return 2*x

assert(double.__name__ == 'double')
assert(double.__doc__ == 'Doubles a number.')
print('double == {!r}'.format(double))
print("double.__wrapped__ == {!r}".format(double.__wrapped__))
print(double(4))


# Out[7]:

#     double == <function double at 0x7fa8a408a620>
#     double.__wrapped__ == <function double at 0x7fa8a408a598>
#     Calling double
#     8
# 

# `fuctools.wraps` is much a nicer way of doing the same thing that `decorator_decorator` does above. It's also a shortcut to `functools.update_wrapper` which is essentially the same function. 
# 
# Pratical uses of decorators
# ---------------------------
# 
# * Flask uses decorators for routing -- `@app.route('/', methods=['GET']`
# * nosetest uses them for declaring parameters for test functions -- `@parameters((1,2,3))`
# * They can set up locks with `threading.Lock`
# * Setting up uniformed logging, maybe with different logging levels for each function
# * Give extra context to functions.
# 
# Let's build some.

# In[8]:

from datetime import datetime

def annotate(**kw):
    '''Attach useful metadata to the function such as who authored and when.'''
    def wrapper(f): # no need to use wraps(f) as we're simply passing f through
        for k,v in kw.items():
            setattr(f, k, v)
        return f
    return wrapper

@annotate(reviewed_by='You', review_date=datetime.today())
@annotate(author='Alec Nikolas Reiter', date=datetime(2014, 8, 19))
def random():
    '''Chosen by fair dice roll. Guarenteed to be random.'''
    return 4

print(random.__dict__)


# Out[8]:

#     {'date': datetime.datetime(2014, 8, 19, 0, 0), 'author': 'Alec Nikolas Reiter', 'review_date': datetime.datetime(2014, 8, 26, 0, 15, 4, 334619), 'reviewed_by': 'You'}
# 

# This example demonstrates the ability to *stack* decorators. It's exactly the same as `random = annotate(...)(annotate(...))(random)`. In this case, the original `random` bubbles up to the surface because it simply passes through the `annotate` decorator. However, when stacking decorators that intercept the actual function call, e.g. a closure actually *calls* the function, stacking decorators gets pretty tricky. I'll show this later on.

# In[9]:

from threading import Lock

# NOTE:
# Threading, multiprocessing and ensuring thread safety are *not* my strong suit
# 0/10 recommend the following function as anything more than illustrating a point
 

def synchronize(lock):
    '''Synchronize multiple functions on a single lock'''
    def wrapper(f):
        @wraps(f)
        def locker(*args, **kw):
            lock.acquire()
            try:
                f(*args, **kw)
            finally:
                lock.release()
        return locker
    return wrapper

my_lock = Lock()

@synchronize(my_lock)
def example_a(*args, **kw):
    # Do some interesting stuff here.
    pass

@synchronize(my_lock)
def example_b(*args, **kw):
    # Do other interesting stuff here.
    pass


# You can even use a class as a decorator.

# In[10]:

class wrapper(object):
    '''Wraps a function inside the object.'''
    def __init__(self, f):
        self.f = f
        self.__name__ = f.__name__
        self.__doc__ = f.__doc__
        self.__dict__.update(f.__dict__)
    def __call__(self, *args, **kw):
        return self.f(*args, **kw)
    def __repr__(self):
        return "{!r}".format(self.f)
    
@wrapper
def random():
    '''Determined by fair dice roll.'''
    return 4

print("wrapper's info: ", wrapper.__name__, wrapper.__doc__)
print("wrapped random's info: ", random.__name__, random.__doc__, random())


# Out[10]:

#     wrapper's info:  wrapper Wraps a function inside the object.
#     wrapped random's info:  random Determined by fair dice roll. 4
# 

# In[11]:

from itertools import islice

class memoize(wrapper):
    '''Decorates a function as to cache it's input and output.'''
    def __init__(self, f):
        self.lookup = {}
        super().__init__(f)
    
    def __call__(self, *args, **kw):
        key = "{!r}{!r}".format(args, kw)
        if key not in self.lookup:
            print("Caching args ({!s}) and result now.".format(key))
            self.lookup[key] = self.f(*args, **kw)
        return self.lookup[key]

def _fib():
    yield from range(2)
    a,b = range(2)
    while True:
        yield a+b
        a, b = b, a+b
    
@memoize
def fib(n):
    return next(islice(_fib(), n, None))

@memoize
def mul(x, y=1):
    return x*y

print('4th Fibonacci number: ', fib(4))
print('5th Fibonacci number: ', fib(5))
print('5th Fibonacci number: ', fib(5))
print('Fibonacci cache lookup: ',  fib.lookup)
print('-'*20)
print('mul(x=3): ', mul(x=3))
print('mul(3):', mul(3))
print('mul cache lookup: ', mul.lookup)


# Out[11]:

#     Caching args ((4,){}) and result now.
#     4th Fibonacci number:  3
#     Caching args ((5,){}) and result now.
#     5th Fibonacci number:  5
#     5th Fibonacci number:  5
#     Fibonacci cache lookup:  {'(5,){}': 5, '(4,){}': 3}
#     --------------------
#     Caching args ((){'x': 3}) and result now.
#     mul(x=3):  3
#     Caching args ((3,){}) and result now.
#     mul(3): 3
#     mul cache lookup:  {'(3,){}': 3, "(){'x': 3}": 3}
# 

# This function would be helpful for attempting to contact a rate limited API. An alternative (and more common implementation) would accept a list of exceptions you'd expect to encounter and handle them as part of the back off process.

# In[12]:

from time import sleep

def retry(times=3, delay=1, backoff=2, exc=Exception, false=False):
    def wrapper(f):
        @wraps(f)
        def trier(*args, **kw):
            _delay = delay
            for attempt in range(times):
                result = f(*args, **kw)
                if result or (false and not result):
                    return result
                sleep(_delay)
                _delay = _delay * backoff
            else:
                raise exc("Attempted {!r} {!r} times, failed to return result".format(f, times))
        return trier
    return wrapper

@retry(false=True)
def _none():
    return None

print("Successfully returned {!r}".format(_none()))

@retry(times=1, delay=1, exc=StopIteration)
def _none():
    return None

try:
    _none()
except (StopIteration,) as e:
    print(e)
    


# Out[12]:

#     Successfully returned None
#     Attempted <function _none at 0x7fa8a408a378> 1 times, failed to return result
# 

# In[13]:

def register_hooks(*hooks):
    '''Register wrapped onto hooks at definition time.
    '''
    def register(f):
        '''Register wrapped onto hooks via hook.register
        
        Sets an attribute on the wrapped indicated that it's hooked
        and another attribute linking the attached hooks.
        '''
        for h in hooks:
            h.register(f)
        setattr(f, '__registered__', True)
        setattr(f, '__watchers__', hooks)
    
    def wrapper(f):
        '''Check if wrapped is registered already.'''
        if not hasattr(f, '__registered__'):
            register(f)
        
        @wraps(f)
        def run(*args, **kw):
            '''Actually run the function and report back.
            
            Realistically, you'd do this in an async way.
            '''
            res = f(*args, **kw)
            for h in f.__watchers__:
                h.run(f, res)
            return res
        
        return run
    return wrapper
    
    
class hook(object):
    '''Dummy hook object.
    
    There's plenty of interesting stuff you could do here.
    '''
    def __init__(self, name):
        self.name = name
    
    def register(self, f):
        print("Registered {!r} on {!r}".format(f, self))
    
    def run(self, f, res):
        print("{!r} reporting that {!r} returned {!r}".format(self, f, res))
        
    def __repr__(self):
        return '<Hook: {!r}>'.format(self.name)
    
    __str__ = __repr__

@register_hooks(hook(name='foo_watcher'), hook(name='foo_reactor'))
def foo(*args, **kw):
    return 3.14

print('\n{!r}'.format(foo))
print('\nWatchers of foo: ')
print(*foo.__watchers__, sep='\n')
print('\nRunning foo()', foo())
print('\n{!r}'.format(foo))


# Out[13]:

#     Registered <function foo at 0x7fa8a4079a60> on <Hook: 'foo_watcher'>
#     Registered <function foo at 0x7fa8a4079a60> on <Hook: 'foo_reactor'>
#     
#     <function foo at 0x7fa8a4079f28>
#     
#     Watchers of foo: 
#     <Hook: 'foo_watcher'>
#     <Hook: 'foo_reactor'>
#     <Hook: 'foo_watcher'> reporting that <function foo at 0x7fa8a4079a60> returned 3.14
#     <Hook: 'foo_reactor'> reporting that <function foo at 0x7fa8a4079a60> returned 3.14
#     
#     Running foo() 3.14
#     
#     <function foo at 0x7fa8a4079f28>
# 

# When you're stacking decorators, you must be careful to remember how they're evaluated: bottom up. Which reflects the inside-out evaluation of what they perform. Follow along here...

# In[14]:

@register_hooks(hook(name='fib_watcher')) # applied last, registers hook classes and intercepts function calls to report back
@memoize # applied second, applies a basic cache and intercepts function calls
@annotate(author='Alec Nikolas Reiter', date=datetime(2014, 8, 19)) # applied first, adds basic metadata attributes
def fib(n):
    return next(islice(_fib(), n, None))

print("Tenth Fibonacci Number: ", fib(10))
print("Tenth Fibonacci Number: ", fib(10))
print(fib.lookup)
print("{!r} created by {!r} on {!r}".format(fib, fib.author, fib.date))


# Out[14]:

#     Registered <function fib at 0x7fa8a409bae8> on <Hook: 'fib_watcher'>
#     Caching args ((10,){}) and result now.
#     <Hook: 'fib_watcher'> reporting that <function fib at 0x7fa8a409bae8> returned 55
#     Tenth Fibonacci Number:  55
#     <Hook: 'fib_watcher'> reporting that <function fib at 0x7fa8a409bae8> returned 55
#     Tenth Fibonacci Number:  55
#     {'(10,){}': 55}
#     <function register_hooks.<locals>.wrapper.<locals>.run at 0x7fa8a409ba60> created by 'Alec Nikolas Reiter' on datetime.datetime(2014, 8, 19, 0, 0)
# 

# That last lines demonstrates exactly what makes working with decorators difficult. Sure, the extra metadata made it through but the ultimate representation is coming from the `register_hooks` decorator despite the fact we were careful to use `wraps` all the way up when necessary.
# 
# Decoratoring Methods and Classes
# --------------------------------
# 
# Since class methods are essentially functions, they can be decorated as well. Though, it's a little trickier if you intend to intercept calls to the method. 

# In[15]:

class Thing(object):
    @annotate(author='Alec Nikolas Reiter', date=datetime(2014, 8, 19))
    def __init__(self, name):
        self.name = name
    
    @memoize # boom!
    def roar(self, phrase):
        return "{}!!!".format(phrase.upper())

ben_grimm = Thing('Ben Grimm')
    
print(Thing.__init__.author)

try:
    print(ben_grimm.roar(phrase="IT'S CLOBBERING TIME!"))
except TypeError as e:
    print("Boom!", e)


# Out[15]:

#     Alec Nikolas Reiter
#     Caching args ((){'phrase': "IT'S CLOBBERING TIME!"}) and result now.
#     Boom! roar() missing 1 required positional argument: 'self'
# 

# You can even wrap objects. For example, this'll create an extremely basic identity map that'll always return the same object when the same arguments are passed in.

# In[16]:

from functools import partial

class objectmemo(memoize):
    def __get__(self, obj, objtype):
        '''Support for instance methods.'''
        return partial(self.__call__, obj)

@objectmemo
class Thing(object):
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kw):
        print(self.name)
    def roar(self):
        print("It's *CLOBBERING* Time!")

ben_grimm = Thing(name="Ben Grimm")
same_thing = Thing(name="Ben Grimm")
different_but_the_same = Thing("Ben Grimm")

assert(ben_grimm is same_thing)
assert(ben_grimm is not different_but_the_same)
ben_grimm()
different_but_the_same()
ben_grimm.roar()


# Out[16]:

#     Caching args ((){'name': 'Ben Grimm'}) and result now.
#     Caching args (('Ben Grimm',){}) and result now.
#     Ben Grimm
#     Ben Grimm
#     It's *CLOBBERING* Time!
# 

# Of course, you'd likely want to check if `Thing("Ben Grimm")` and `Thing(name="Ben Grimm")` return the same object (the same issue with the `memoize` class for functions, too) and overall much more finer grained control over the cache. Perhaps even creating a generalized `memoize` class that is instanstiated and then tracks a cache for each individual object passed into it. This would allow you to clear individual areas of the cache.

# In[17]:

from collections import defaultdict

class Memoize(object):
    def __init__(self):
        self.cache = defaultdict(dict)
    
    def __call__(self, obj):
        @wraps(obj)
        def cacher(*args, **kw):
            nonlocal self
            key = "{!r}{!r}".format(args, kw)
            if key not in self.cache[obj.__name__]:
                self.cache[obj.__name__][key] = obj(*args, **kw)
            return self.cache[obj.__name__][key]
        return cacher

memo = Memoize()
    
@memo
class Point(object):
    '''Represents a point in Euclidean space.'''
    def __init__(self, x, y):
        self.x  = x
        self.y = y
    
    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y)

@memo
def is_even(n):
    '''Checks if a number is even'''
    return not n%2

_34 = Point(3,4)
_68 = Point(3,4) + Point(3,4)

print(Point.__name__, ': ', Point.__doc__)
print(is_even.__name__, ': ', is_even.__doc__)

assert(_34 is Point(3,4))
print(is_even(5))
print(is_even(34))
print(memo.cache)
del memo.cache['Point']
assert(_34 is not Point(3,4))
print(memo.cache)


# Out[17]:

#     Point :  Represents a point in Euclidean space.
#     is_even :  Checks if a number is even
#     False
#     True
#     defaultdict(<class 'dict'>, {'is_even': {'(5,){}': False, '(34,){}': True}, 'Point': {'(3, 4){}': <__main__.Point object at 0x7fa8a40a2fd0>, '(6, 8){}': <__main__.Point object at 0x7fa8a40a2eb8>}})
#     defaultdict(<class 'dict'>, {'is_even': {'(5,){}': False, '(34,){}': True}, 'Point': {'(3, 4){}': <__main__.Point object at 0x7fa8a40410f0>}})
# 

# Fin
# ---
# 
# That's all I have for now. Hopefully, this has been informational and illustrated more than just *what* decorators as but also what they can be used for.
# 
# If you're wanting more information about decorators, there is:
# 
# * [PEP 318](http://legacy.python.org/dev/peps/pep-0318/) which covers the exact syntax
# * The [Python Decorator Library](https://wiki.python.org/moin/PythonDecoratorLibrary) a collection of example decorators at Python.org 
# * This [series of blog posts](http://blog.dscpl.com.au/search/label/decorators) by Graham Dumpleton -- author of wrapt
# * The [wrapt](http://wrapt.readthedocs.org/en/latest/) and [decorator](http://micheles.googlecode.com/hg/decorator/documentation3.html) packages, which are both tools to ease the development and use of decorators (as well as a few other things).
# * As well as [a whole host of results](https://www.google.com/search?btnG=1&pws=0&q=python+decorators&gws_rd=ssl) on Google for "python decorator" -- because every Python developer and their mother has blogged about this very thing.
