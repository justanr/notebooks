
# coding: utf-8

# In[1]:

def countdown(n):
    print("Count down from", n)
    while n >= 0:
        newvalue = (yield n)
        if newvalue is not None:
            n = newvalue
        else:
            n -= 1

c = countdown(5)

flagged = False

for n in c:
    print(n)
    if n == 3 and not flagged:
        print(c.send(5))
        flagged = True


# In[ ]:



