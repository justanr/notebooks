
# In[1]:

from itertools import chain

class IterInt(int):
    
    def __iter__(self):
        yield self

def countdown(n):
    n = IterInt(n)
    if n < 0:
        return "Countdown finished"
    else:
        yield from chain(n, countdown(n-1))

list(countdown(10))


# Out[1]:

#     [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Today I learned that setting and overriding methods and attributes on built in types is a `TypeError`. Maybe it's to make iterating over an integer feel wrong. But if this is wrong, I don't want to be right.
