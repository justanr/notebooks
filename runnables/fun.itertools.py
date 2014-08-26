
# Originally, I saw this issue in a post on /r/learnpython:
# 
#     '''
#     if (n%a==0) or (n%b==0) or (n%c==0) or (n%ab==0) or (n%ac==0) or (n%bc==0) or (n%abc==0):
#         print "Yes."
#     else:
#         print "No."
#     '''
# 
# The original poster was seeking advice on why this was throwing a `NameError`. Turns out, what he really wanted was to find out if n divided evenly by a, b, c or any combination of a, b and c.
# 
# My first suggestion was to use any/all.

# In[1]:

# pick a number, any numbers
n = 15
a = 1
b = 2
c = 3

if any(not n%x for x in [a,b,c, a*b, a*c, c*b, a*b*c]):
    print("Yes.")
else:
    print("No.")


# Out[1]:

#     Yes.
# 

# Which works. But could you imagine being the guy who gets this code and is tasked with adding `d = 4` to this mix? Forbid `e = 5` or `f = 6`.

# In[2]:

import itertools as it

def powerset(iterable):
    '''Courtesy of the itertools documentation.'''
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s,r) for r in range(1, len(s)+1))


# Enter itertools: a tool box of fun. This function returns powersets. That is given `range(1,4)` it'll output `(1,), (2,), (3,), (1,2), (1,3), (2,3), (1,2,3)`. The original itertools documentation actually has `range(0, len(s)+1)` but that causes the first set to be `(,)` -- which I consider to be useless in this instance (despite being a valid set result). So, let's rewrite that conditional.

# In[3]:

from functools import partial, reduce
from operator import mul

f = partial(reduce, mul)

if any(not n%f(x) for x in powerset(range(1,4))):
    print("Yes.")
else:
    print("No.")


# Out[3]:

#     Yes.
# 

# Now imagine being the guy tasked to extend the range from 3 to 6. You change one integer: `range(1,7)`. However, we'll likely want to do something with the valid results from that test. 

# In[4]:

def do_thing(*stuff):
    '''A dummy functions.'''
    print("Yes.")

sets, selectors = it.tee(powerset(range(1,4)))
selectors = (not n%f(x) for x in selectors)
wanted = list(it.compress(sets, selectors))

if any(wanted):
    do_thing()


# Out[4]:

#     Yes.
# 

# How this works is that `it.tee` produces a number of iterables from the original iterable -- you can change the number by passing a second value to tee. However, you must be careful with tee. If you advance the original iterable, you advanced the tee'd iterables as well -- most likely prematurely. But, since we're generating the iterable directly into it instead of passing a stored iterable, we can't do that (well, you could but that's black magic).
# 
# What compress does is accept an iterable of data and an iterable of truthy values. The same result could be had with either `filter` or `it.filterfalse`.

# In[5]:

filterd, filterfd = it.tee(powerset(range(1,4)))

filterd = list(filter(lambda x: not n%f(x), filterd))
filterfd = list(it.filterfalse(lambda x: n%f(x), filterfd))

print(wanted == filterd == filterfd)


# Out[5]:

#     True
# 

# You can also use itertools to divide up iterable based on a variety of things:
# 
# * into values that are True/False based on a key.
# * into a set of values until a false one, a set of values after (and including) the first false one

# In[6]:

def partition(iterable, key):
    t, f = it.tee(iterable)
    return filter(key, t), it.filterfalse(key, f)

def divide(iterable, key):
    t, f = it.tee(iterable)
    return it.takewhile(key, t), it.dropwhile(key, f)

parted = partition(powerset(range(1,4)), lambda x: not n%f(x))
divided = divide(powerset(range(1,4)), lambda x: not n%f(x))

print("-"*20)
print("partition(powerset(range(1,4)), lambda x: not n%f(x))", list(map(list, parted)), sep="\n")
print("-"*20)
print("divide(powerset(range(1,4)), lambda x: not n%f(x))", list(map(list, divided)), sep="\n")
print("-"*20)


# Out[6]:

#     --------------------
#     partition(powerset(range(1,4)), lambda x: not n%f(x))
#     [[(1,), (3,), (1, 3)], [(2,), (1, 2), (2, 3), (1, 2, 3)]]
#     --------------------
#     divide(powerset(range(1,4)), lambda x: not n%f(x))
#     [[(1,)], [(2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]]
#     --------------------
# 

# We can also divy up the sets based on their product by way of `collections.defaultdict` and `it.groupby`

# In[7]:

from collections import defaultdict

store = defaultdict(list)
for k, g in it.groupby(powerset(range(1,4)), key=f):
    # g will be a grouper iterable that must be consumed
    store[k].extend(g)

print(store)


# Out[7]:

#     defaultdict(<class 'list'>, {1: [(1,)], 2: [(2,), (1, 2)], 3: [(3,), (1, 3)], 6: [(2, 3), (1, 2, 3)]})
# 

# Retrieving the desired information from this store is a little more involved, however.

# In[8]:

wanted = [v for k, v in store.items() if not n%k]

print('-'*20)
print("Raw list:", wanted)
print('-'*20)
print("it.chain(*wanted)", list(it.chain(*wanted)))
print('-'*20)
print("it.chain.from_iterable(wanted)", list(it.chain.from_iterable(wanted)))


# Out[8]:

#     --------------------
#     Raw list: [[(1,)], [(3,), (1, 3)]]
#     --------------------
#     it.chain(*wanted) [(1,), (3,), (1, 3)]
#     --------------------
#     it.chain.from_iterable(wanted) [(1,), (3,), (1, 3)]
# 

# The difference between `it.chain(*wanted)` and `it.chain.from_iterable(wanted)` is that the former is eager and the later is lazy. In this particular instance, we're consuming the iterator immediately either way and it's a basic list. However, with more expensive operations -- say we had a list of generators that each returned the results of floating point math -- you'd want the results to be as lazy as possible.
