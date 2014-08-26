
# Cards Against Humanity is a pretty awesome game, especially if you're friends have a dark sense of humor and optionally beer. Think of it like Apples to Apples for horrible people. If you've never heard of either of them, I'd recommend picking them up.
# 
# The rules for these games is pretty simple:
# 
# * You have two types of cards: Black and White for Cards Against Humanity, Red and Green for Apples to Apples
# * Each player draws a hand of white or red cards
# * Each player takes a turn as the judge of the round, who draws a single black or green card
# * The other players play a card or cards from their hand
# * The winner gets the black/red card, players draw cards and the next player becomes the judge
# 
# For the sake of this post, I'll be modeling Cards Against Humanity, since it's a tiny bit more interesting to model than Apples to Apples
# 
# Step One: Cards
# ---------------
# It's always best to start with your basic bits. At least that's how I look at it. In this case, it's the cards. Since cards never change, it's best to model them with an immutable data type. Tuples are the most obvious choice, but card[0] is less descriptive than card.text, so collections.namedtuple is a better choice.

# In[1]:

from collections import namedtuple

WhiteCard = namedtuple('WhiteCard', 'text', verbose=False)
BlackCard = namedtuple('BlackCard', ['text', 'pick', 'draw'], verbose=False)

blacktexts = ['{} nested inside {}', 'from {} import {}', "implementing {} only to find it's in {}"]
blackcards = [BlackCard(*fields) for fields in [(text, text.count('{}'), text.count('{}')) for text in blacktexts]]
whitecards = [WhiteCard(text) for text in ['itertools', 'a list comprehension', 'a dict comprehension', 
                                           'a generator comprehension', '*', 'functools', 'the standard library', 
                                           'reduce', 'map', 'doubly linked list', 'collections']]


# And to play them, we simply run the following.

# In[2]:

from random import shuffle

shuffle(blackcards)
shuffle(whitecards)

card = blackcards.pop()
card.text.format(*[c.text for c in whitecards[:card.pick]])


# Out[2]:

#     "implementing reduce only to find it's in *"

# Step Two: Decks
# ---------------
# The next step is to model the decks for black cards, white cards, the discard piles and players' hands. The biggest problem we'll have here is that while players' hands are essentially the same thing as a deck, they have a limited length. Of course we could manage the length by hand, or we could use deque.

# In[3]:

from collections import deque

max_cards = 2
players = 3

hands = [deque([whitecards.pop() for _ in range(max_cards)], maxlen=max_cards) for _ in range(players)]

blackdiscard = []
whitediscard = []


# Step Four: A Minimal Automated Play Through
# -------------------------------------------
# 
# No player interaction here, just testing that pieces fit together as expected.

# In[4]:

from random import choice
from itertools import chain

max_cards = 5

white_text = ['itertools', 'functools', 'fiboncci sequence', 'WSGI', 
              'list comprehensions', 'Javascript', 'RESTful', 'C++', 'messy inheritance', 
              'an unclear variable name', "a class that's actually just a closure", 
              'overriding a built in', 'Java style getters and setters', 'Ruby', 
              'a blank except line', 'dynamic imports', 'braces', '__future__', 'a lambda', 
              'beautiful and idiomatic', 'Pythonic', 'spam', 'eggs', 'wheels', 'distribute'
              ]

blacktexts = ['{} nested inside {}', 'from {} import *', 'from {} import {}', 'Using Python with {}', 
              "Implementing {} to find it's in the standard library",  'Treating Python like {}',  'Python: The Old {}', 
              'The next feature Guido should implement is {}',  '{} in Python is like {}']

black_builder = [(text, text.count('{}'), text.count('{}')) for text in blacktexts]

whitecards = [WhiteCard(text) for text in white_text]
blackcards = [BlackCard(*fields) for fields in black_builder]

shuffle(whitecards)
shuffle(blackcards)

hands = [deque((whitecards.pop() for _ in range(max_cards)), maxlen=max_cards) for _ in range(players)]

choices = []

while blackcards:
    card = blackcards.pop()
    picked = [[hand.pop() for _ in range(card.pick)] for hand in hands]
    
    if not len(whitecards) >= len(hands) * card.draw:
        whitecards.extend(whitediscard)
        whitediscard = []
    
    for hand in hands:
        hand.extend([whitecards.pop() for _ in range(card.draw)])
    
    played = [card.text.format(*[c.text for c in pick]) for pick in picked]
    choices.append(choice(played))
    
    blackdiscard.append(card)
    whitediscard.extend(chain.from_iterable(picked))

for c in choices:
    print(c)
        


# Out[4]:

#     Using Python with a blank except line
#     from itertools import a class that's actually just a closure
#     beautiful and idiomatic nested inside Ruby
#     Implementing C++ to find it's in the standard library
#     The next feature Guido should implement is messy inheritance
#     from C++ import *
#     Treating Python like wheels
#     WSGI in Python is like a class that's actually just a closure
#     Python: The Old beautiful and idiomatic
# 

# Of course, if you wanted to continually run through the whole thing, you could set that up.

# In[5]:

from functools import partial

whitecards = [WhiteCard(w) for w in white_text]
blackcards = [BlackCard(*fields) for fields in black_builder]

Hand = partial(deque, maxlen=max_cards)

def main():
    global blackcards, whitecards, whitediscard, blackdiscard
    while True:
        shuffle(blackcards)
        shuffle(whitecards)
        print("Dealing hands.")
        hands = [Hand(whitecards.pop() for _ in range(max_cards)) for _ in players]
        card = blackcards.pop()
        
        picked = [[h.pop() for _ in range(card.pick)] for h in hands]
        
        if not len(whitecards) >= len(hands) * card.draw:
            whitecards.extend(whitediscard)
            whitediscard.clear()
        
        for hand in hands:
            hand.extend(whitecards.pop() for _ in range(card.draw))
        
        for pick in picked:
            print(card.text.format(*[c.text for c in pick]))
            input("")
        
        blackdiscard.append(card)
        whitediscard.extend(chain.from_iterable(picked))
    
    print("Out of black cards. Restocking decks.")
    blackcards.extend(blackdiscard)
    whitecards.extend(whitediscard)
    whitecards.extend(chain.from_iterable(hands))
    blackdiscard.clear()
    whitediscard.clear()


# Is it ugly? Yeah -- code that's duplicated, globals, places where tools like map would be clean it up, and just generally a mess. But for a proof of concept -- building a basic CAH clone in Python -- it's alright. Though, I'll definitely be spending some time cleaning it up and improving it.
