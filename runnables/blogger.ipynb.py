
# [IPython](http://ipython.org/) is a powerful, interactive shell for Python, considered by many to be a replacement for the standard Python shell. It's most likely in your repositories under `ipython` (or `ipython3` or `ipython2` depending on which Python version is native to your distro). There's tons of information available and it's highly customizable -- even coming with support languages other than Python.

# In[1]:

get_ipython().run_cell_magic('bash', '', 'echo "Hello from $BASH"')


# Out[1]:

#     Hello from /bin/bash
# 

# But what I'm really going to evangelize today is the [Notebook](http://ipython.org/notebook.html) portion of it. You'll probably have to install the notebook separately -- typically listed under `ipython-notebook` in repositories. In fact, I'm blogging from it right now.

# What is a Notebook
# ------------------
# A Notebook is a portable IPython session that runs in your browser. When you run `ipython notebook` it starts a local server and it'll probably attempt to launch a browser, too. If not, open one up and navigate to `127.0.0.1:8888` and you'll see the IPython Notebook dashboard, which'll list all the notebooks in the directory it was launched in and allow you create new ones, run present ones and even delete them.
# 
# In many ways, a Notebook is just like using IPython on the commandline. Code in run cells is available to cells below it. You can even use IPython's magics in them.

# Sharing Notebooks
# -----------------
# IPython stores Notebooks in `ipynb` files -- JSON by any other name -- in the directory that the Notebook server was launched in. From there, you can store them on Github, send them to friends, host a Notebook Viewer server yourself, 
# 
# Also, you can convert the Notebooks to other formats: markdown, HTML, Latex, PDF, reStructured Text, javascript slides, and actual Python files. To do so, you simply run: `ipython nbconvert --to {format} [FILE]`. However, you may have to install the `pacdoc` package to do so (I did). I'll be covering converting them to HTML and using them with [Google's Blogger platform](http://www.blogger.com)

# Blogging with IPython Notebooks
# -------------------------------
# The first step is to, of course, actually produce an IPython Notebook. You already know how, so just do it.
# 
# After you have your notebook, pandoc is installed, and you're sitting with a terminal open, you'll want to run `ipython nbconvert --to html mynb.ipynb`. This'll generate a full HTML page complete with CSS and the necessary Javascript to display mathematical equations. You'll want to extract this CSS and Javascript and place it into your Blogger template.
# 
# ###Modifying Blogger Templates
# To do this, I actually didn't use vim, I used the text editor that came with Mint. Simply paste this CSS into the template by going in through `Template > Customize > Advanced > Add CSS`. And then the Javascript by going in through `Template > Edit HTML` and pasting it in somewhere in the `<head>` tag.
# 
# ###Translating Notebooks to HTML
# To get just the body of the Notebook in HTML form, use `ipython nbconvert --to html --template basic mynb.ipynb`.  Then simply copy the generated HTML into the HTML portion of a new Blogger post. If you use Linux, there's actually a fairly simple way of doing this on the command line: xclip. `xclip -selection c mynb.html`. Alternatively, if you don't care if the actual HTML file is generated you can just run `ipython nbconvert --to html --template basic --stdout mypy.ipynb | xclip -selection c`. Then simply CRTL-V in the HTML editor for blogger and click Publish.
