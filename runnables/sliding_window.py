
# A sliding window is a type of function that accepts an iterable and sends it back in overlapping chunks. This is useful when you need to process an item in context. There's one in the *old* library examples for itertools (I'm talking Python v. 2.3.5)

# In[1]:

from itertools import islice

def old_window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

get_ipython().magic("timeit -n 1000 -r 5 list(old_window('abcdefgh', 3))")
print(*list(old_window('abcdefgh', 3)), sep='\n')


# Out[1]:

#     1000 loops, best of 5: 3.4 µs per loop
#     ('a', 'b', 'c')
#     ('b', 'c', 'd')
#     ('c', 'd', 'e')
#     ('d', 'e', 'f')
#     ('e', 'f', 'g')
#     ('f', 'g', 'h')
# 

# The New Hotness
# ---------------
# But that's old and if Node, Rust, Go and Mongo have taught me anything, it's anything more than 10 seconds old is garbage and not webscale. Sarcasm aside, I just enjoy tearing things down just to rebuild them and hopefully learn something in the process. Let's see what we can come up with...

# In[2]:

from itertools import tee

def window(it, size=3):
    yield from zip(*[islice(it, s, None) for s, it in enumerate(tee(it, size))])

get_ipython().magic("timeit -n 1000 -r 5 list(window('abcedefgh', 4))")
print(*list(window('abcedefgh', 4)), sep='\n')


# Out[2]:

#     1000 loops, best of 5: 6.7 µs per loop
#     ('a', 'b', 'c', 'e')
#     ('b', 'c', 'e', 'd')
#     ('c', 'e', 'd', 'e')
#     ('e', 'd', 'e', 'f')
#     ('d', 'e', 'f', 'g')
#     ('e', 'f', 'g', 'h')
# 

# Okay, so it's about half as fast (or twice as slow, I'm not sure which is the Glass Half Full).
# 
# Let's deconstruct it first:
# 
# * First the iterable is cloned a number of times.
# * Those iterables are then passed to enumerate which is a generator that returns an item and it's position in an iter
# * The positions and iterables are then passed into a list comphrension loop
# * The loop populates the list with a series of islice objects -- each starting an iterable at the position given to it by enumerate
# * The list is splatted into zip
# * `yield from` the zip
# 
# But it's one line! One liners are cool. Right?

# Benchmarks Mean Nothing
# -----------------------
# I'm of the opinion that benchmarks don't prove much by themselves -- a broader context is needed.
# 
# However... let's see how it stacks up against the old window in a variety of situations.

# In[3]:

# calculate rolling average

from operator import add
from functools import reduce

f = lambda x: reduce(add, x)/len(x)

print(list(map(f, window(range(10), size=4))))
get_ipython().magic('timeit -n 1000 -r 5 list(map(f, old_window(range(10), n=4)))')
get_ipython().magic('timeit -n 1000 -r 5 list(map(f, window(range(10), size=4)))')


# Out[3]:

#     [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
#     1000 loops, best of 5: 10.1 µs per loop
#     1000 loops, best of 5: 14.3 µs per loop
# 

# In[4]:

# generate pseudo text markov chains

text = "mary had a little lamb"

print({c[:-1]:c[-1] for c in window(text.split(), 3)})
get_ipython().magic('timeit -n 1000 -r 5 {c[:-1]:c[-1] for c in window(text.split(), 3)}')
get_ipython().magic('timeit -n 1000 -r 5 {c[:-1]:c[-1] for c in old_window(text.split(), 3)}')


# Out[4]:

#     {('had', 'a'): 'little', ('a', 'little'): 'lamb', ('mary', 'had'): 'a'}
#     1000 loops, best of 5: 14.8 µs per loop
#     1000 loops, best of 5: 5.14 µs per loop
# 

# Annother application for this in as a solution to Euler 8.

# In[5]:

from collections import deque
from itertools import chain
from functools import partial
from operator import mul

nums = """73167176531330624919225119674426574742355349194934
96983520312774506326239578318016984801869478851843
85861560789112949495459501737958331952853208805511
12540698747158523863050715693290963295227443043557
66896648950445244523161731856403098711121722383113
62229893423380308135336276614282806444486645238749
30358907296290491560440772390713810515859307960866
70172427121883998797908792274921901699720888093776
65727333001053367881220235421809751254540594752243
52584907711670556013604839586446706324415722155397
53697817977846174064955149290862569321978468622482
83972241375657056057490261407972968652414535100474
82166370484403199890008895243450658541227588666881
16427171479924442928230863465674813919123162824586
17866458359124566529476545682848912883142607690042
24219022671055626321111109370544217506941658960408
07198403850962455444362981230987879927244284909188
84580156166097919133875499200524063689912560717606
05886116467109405077541002256983155200055935729725
71636269561882670428252483600823257530420752963450"""

nums = [int(n) for n in chain.from_iterable(nums.split("\n"))]

def euler_8_1(numbers):
    limit = 13
    run = []
    largest = 0
    
    # originally this was a while-loop that popped off items from numbers
    # I changed for the sake of not being so fucking stupid
    # inserting at index[0] on a list is still dumb though.
    
    # purpose for this change was to avoid copying the 
    # numbers list every time and thus artificially
    # bloating the run time for the solution
    
    # This was my first encounter with windowing
    # through I didn't know it yet.
    
    for n in numbers:
        run.insert(0, n)
        if len(run) > limit:
            run.pop()
        
        x = reduce(lambda x, y: x*y, run)
        if x > largest:
            largest = x
    return largest

def euler_8_2(numbers):
    run = deque(maxlen=13)
    largest = 0
    for n in nums:
        # look another window
        # still didn't really know  what
        # windowing was at this time
        run.append(n)
        x = reduce(mul, run)
        
        if x > largest:
            largest = x
    
    return largest

print("Solution to Euler #8 (as of 8/21/14): ", max(map(partial(reduce, mul), window(nums, size=13))))
get_ipython().magic('timeit -n 1000 -r 5 euler_8_1(nums)')
get_ipython().magic('timeit -n 1000 -r 5 euler_8_2(nums)')
get_ipython().magic('timeit -n 1000 -r 5 -p 5 max(map(partial(reduce, mul), window(nums, size=13)))    # upped the precision of these two')
get_ipython().magic("timeit -n 1000 -r 5 -p 5 max(map(partial(reduce, mul), old_window(nums, n=13)))   # because they're pretty close")


# Out[5]:

#     Solution to Euler #8 (as of 8/21/14):  23514624000
#     1000 loops, best of 5: 2.53 ms per loop
#     1000 loops, best of 5: 1.05 ms per loop
#     1000 loops, best of 5: 1.2112 ms per loop
#     1000 loops, best of 5: 1.2605 ms per loop
# 

# Not too shabby, not *quite* as fast as the second iteration of my solution but way faster than my first (admittedly, stupid) solution. The old windowing function falls *just short* of the new one.

# Windowing Infinite Generators
# -----------------------------
# The real differences start to be seen here: working with infinite generators. The old windowing function handles this quite well, assuming you don't attempt to consume "entire" generator at once. The new windowing function needs you to massage the infinite generator into a subset. Either way, `islice` comes into play, it's just a matter of where.

# In[6]:

def fib():
    yield from range(2)
    a,b = range(2)
    while True:
        yield a+b
        a,b = b, a+b

size = 5
start = 0
end = 9

def display(it):
    print(*list(it), sep='\n')

display(window(islice(fib(), start, end), size))


# Out[6]:

#     (0, 1, 1, 2, 3)
#     (1, 1, 2, 3, 5)
#     (1, 2, 3, 5, 8)
#     (2, 3, 5, 8, 13)
#     (3, 5, 8, 13, 21)
# 

# That's pretty nifty. However, `window` still creates a number of iterators equal to it's window size and partially consumes them almost immediately. And we can't ask for, say the first five windows of five numbers without jumping throw some nasty hoops as opposed to the old windowing function:

# In[7]:

size = 5
frames = 5

# what is this hy? -- https://github.com/hylang/hy
display(map(next,(window(islice(fib(), i, i+size), size) for i in range(frames)))) 
#islice(old_window(fib(), size), frames)


# Out[7]:

#     (0, 1, 1, 2, 3)
#     (1, 1, 2, 3, 5)
#     (1, 2, 3, 5, 8)
#     (2, 3, 5, 8, 13)
#     (3, 5, 8, 13, 21)
# 

# Let's break that down, because even though I wrote it just now, I have a hard time following it (and it only took about ten tries to get it right, too):
# 
# * `islice(fib(), i, i+size)` -- slice the number generator at an arbitrary length
# * `window(..., size)` -- window that sliced generator to the appropriate size
# * `... for i in range(frames)` generate the arbitrary numbers for the original islice
# * `(...)` wrap the whole thing in a generator expression
# 
# As opposed to the *old busted,* which breaks down to:
# 
# * `old_window(fib(), size)` -- begin windowing the generator
# * `islice(..., frames)` -- only take the frames that we want.
# 
# Starting the generator in an arbitrary spot isn't as intuitive as it is with the old windower - which is just fast forward the generator to a specific spot with islice. With the *new hotness* we have to make sure we're offsetting appropriately (only took three tries and some serious mind searching to determine if I was simply retarded or not).

# In[8]:

start = 3
size = 5
frames = 5

#list(map(next,(window(islice(fib(), i+start, i+size+start), size) for i in range(frames))))
display(islice(old_window(islice(fib(), start, None), n=size), frames))


# Out[8]:

#     (2, 3, 5, 8, 13)
#     (3, 5, 8, 13, 21)
#     (5, 8, 13, 21, 34)
#     (8, 13, 21, 34, 55)
#     (13, 21, 34, 55, 89)
# 

# Everything Old Is New
# ---------------------
# Okay, so using a single container is faster than yielding out a bunch of iterators. But why not use a fixed length iterable instead of playing surgeon on a tuple? `collections.deque` is one of my favorite things in the standard library and it's fixed length and I (accidentally) used it for windowing before. Why not general purpose it?

# In[9]:

def dedow(it, size, start=0, stop=None, step=None):
    '''dedow -- `de`que win`dow` -- alright, that's a stupid name.
    Yields a tuple for each frame of the window.
    '''
    it = iter(it)
    if any([start, stop, step]):
        it = islice(it, start, stop, step)
    window = deque(islice(it, size), maxlen=size)
    yield tuple(window)
    for i in it:
        window.append(i)
        yield tuple(window)

display(dedow('abcdefgh', size=3))
get_ipython().magic("timeit -n 1000 -r 5 list(old_window('abcdefgh', n=3))")
get_ipython().magic("timeit -n 1000 -r 5 list(window('abcdefgh', size=3))")
get_ipython().magic("timeit -n 1000 -r 5 list(dedow('abcdefgh', size=3))")


# Out[9]:

#     ('a', 'b', 'c')
#     ('b', 'c', 'd')
#     ('c', 'd', 'e')
#     ('d', 'e', 'f')
#     ('e', 'f', 'g')
#     ('f', 'g', 'h')
#     1000 loops, best of 5: 3.52 µs per loop
#     1000 loops, best of 5: 6.34 µs per loop
#     1000 loops, best of 5: 6.02 µs per loop
# 

# It's actually slower than `window` here, but I find the code much more readable than either window *or* old window. It handles just like the old windowing function, plus it can handle slicing an iterable for you. Though, I do kinda feel that by passing arguments to islice violates the single responsibility principle -- not enough that I'll take it out, but I do see how that could be valid criticism.

# In[10]:

# Window 3 over every other fibonacci number for the first 20 numbers
display(dedow(fib(), size=3, step=2, stop=20))


# Out[10]:

#     (0, 1, 3)
#     (1, 3, 8)
#     (3, 8, 21)
#     (8, 21, 55)
#     (21, 55, 144)
#     (55, 144, 377)
#     (144, 377, 987)
#     (377, 987, 2584)
# 

# Benchmarks Still Means Nothing
# ------------------------------
# Let's benchmark these against some tests:
# 
# 1. Window five values from the first 100 numbers of fib()
# 2. 100 windows of five values from fib()
# 3. Solve Euler 8
# 4. Generate a simple n-Order Markov Chain (n = window size - 1)

# In[11]:

print("1. Window of 5 for first 100 values of fib()")
consume = partial(deque, maxlen=0)
fib100 = tee(islice(fib(), 100), 3)

# we could use dedow's stop kw but, I think it's less fair to construct the slice each interval
get_ipython().magic('timeit -n 1000 -r 5 consume(window(fib100[0], size=5))')
get_ipython().magic('timeit -n 1000 -r 5 consume(dedow(fib100[1], size=5))')
get_ipython().magic('timeit -n 1000 -r 5 consume(old_window(fib100[2], n=5))')

print("\n2. First 100 windows of 5 of fib()")
get_ipython().magic('timeit -n 1000 -r 5 consume((window(islice(fib(), i, i+5), 5) for i in range(100)))')
get_ipython().magic('timeit -n 1000 -r 5 consume(islice(dedow(fib(), size=5), 100))')
get_ipython().magic('timeit -n 1000 -r 5 consume(islice(old_window(fib(), n=5), 100))')

print("\n3. Solve Euler #8")
def solve(prob):
    f = partial(reduce, mul)
    return max(map(f, prob))

get_ipython().magic('timeit -n 1000 -r 5 solve(window(nums, size=13))')
get_ipython().magic('timeit -n 1000 -r 5 solve(dedow(nums, size=13))')
get_ipython().magic('timeit -n 1000 -r 5 solve(old_window(nums, n=13))')

print("\n4. Generate a simple n-Order Markov Chain (n = window size - 1)")
text = 'lorem ipsum dolor sit amet consectetur adipiscing elit pellentesque gravida turpis egestas nisl consectetur et'
get_ipython().magic('timeit -n 1000 -r 5 {c[:-1]:c[-1] for c in window(text.split(), 3)}')
get_ipython().magic('timeit -n 1000 -r 5 {c[:-1]:c[-1] for c in dedow(text.split(), 3)}')
get_ipython().magic('timeit -n 1000 -r 5 {c[:-1]:c[-1] for c in old_window(text.split(), 3)}')


# Out[11]:

#     1. Window of 5 for first 100 values of fib()
#     1000 loops, best of 5: 6.07 µs per loop
#     1000 loops, best of 5: 4.33 µs per loop
#     1000 loops, best of 5: 3.22 µs per loop
#     
#     2. First 100 windows of 5 of fib()
#     1000 loops, best of 5: 91.9 µs per loop
#     1000 loops, best of 5: 78.8 µs per loop
#     1000 loops, best of 5: 54.2 µs per loop
#     
#     3. Solve Euler #8
#     1000 loops, best of 5: 1.22 ms per loop
#     1000 loops, best of 5: 1.45 ms per loop
#     1000 loops, best of 5: 1.27 ms per loop
#     
#     4. Generate a simple n-Order Markov Chain (n = window size - 1)
#     1000 loops, best of 5: 13.2 µs per loop
#     1000 loops, best of 5: 15.5 µs per loop
#     1000 loops, best of 5: 12.3 µs per loop
# 

# Part of the Zen of Python is "There should be one-- and preferably only one --obvious way to do it.". However, windowing isn't something that I find obvious or easy to do as evidenced by three solutions presented here. Aside from the two I presented, I can think of at least one more solution: a class based windower that implements the iterator protocol.

# In[12]:

from collections import namedtuple
from string import ascii_lowercase as letters

# islice doesn't play well with actual slice objects
_slice = namedtuple('_slice', ['start', 'stop', 'step'])
        
class Window:
    '''Implements the iter protocol as to represent a window over a sequence'''
    def __init__(self, seq, size, start=None, step=None, stop=None):
        self.slice = _slice(start or 0, stop or None, step or 1) 
        self.size = size
        self._seq = iter(seq)
        if any(self.slice):
            self._seq = islice(self._seq, *self.slice)
        self.cheat = deque(islice(self._seq, size), maxlen=size)
        self._stop = False
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._stop:
            raise StopIteration
            
        cheat = tuple(self.cheat)
        
        try:
            self.cheat.append(next(self._seq))
        except StopIteration:
            self._stop = True
        
        return cheat

display(dedow(letters, size=4, step=2))
get_ipython().magic('timeit -n 1000 -r 5 consume(Window(letters, size=4, step=2))')
get_ipython().magic('timeit -n 1000 -r 5 consume(dedow(letters, size=4, step=2))')


# Out[12]:

#     ('a', 'c', 'e', 'g')
#     ('c', 'e', 'g', 'i')
#     ('e', 'g', 'i', 'k')
#     ('g', 'i', 'k', 'm')
#     ('i', 'k', 'm', 'o')
#     ('k', 'm', 'o', 'q')
#     ('m', 'o', 'q', 's')
#     ('o', 'q', 's', 'u')
#     ('q', 's', 'u', 'w')
#     ('s', 'u', 'w', 'y')
#     1000 loops, best of 5: 21.5 µs per loop
#     1000 loops, best of 5: 9.73 µs per loop
# 

# Of course, that's a basic example and I (feel like I) cheated by using deque to store the window itself -- I mean, it's basically `dedow`. But it communicates the basic idea behind using an object as a windower.

# Did I Learn Anything?
# ---------------------
# Implementing the iter protocol is difficult sometimes. I tried a bunch of methods until I decided to cheat and use deque. The guys who contribute to Python know more about what's fastest than I do (who saw that coming?). 
# 
# Also, windowing is fun. Why haven't I considered this before for projects? These implementations are actually viable for a Markov Chain project I've been working on occasionally (which up until now had a very awkward method that broke text into tuplekey-value pairs).
