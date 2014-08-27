
# Metadata and You
# ----------------
# You're probably familiar, at least in passing, with the concept of metadata. It's data about data. In terms of audio files, it's things like:
# 
# * Bitrate
# * Duration/Length
# * Artist
# * Album
# * Track Position (if available)
# * Year released (if available)
# 
# Today, I'm using [TinyTag](https://github.com/devsnd/tinytag) (`pip install tinytag`) to extract metadata (and TinyTag only supports this), but there's a whole plethora of libraries to extract and set audio metadata:
# 
# * Mutagen [docs](https://mutagen.readthedocs.org/en/latest/) [source](https://bitbucket.org/lazka/mutagen)
# * eyed3 [docs](http://eyed3.nicfit.net/) [source](https://bitbucket.org/nicfit/eyed3)
# * stagger [source](https://code.google.com/p/stagger/)
# 
# ###Aside
# I actually don't spend a terrible amount of time on actually pulling the metadata out. It's extremely straightforward with TinyTag. I spend more time with processing and massaging that data into information we can really work with. I revisit the cacheing decorator from the decorator post (and don't follow much of my own advice -- it's kind of a do as I say, not as I do sort of thing, even then I'm not even really giving that great of advice) as well as improving on the Artist/Album/Track mock data models from the API post as well. There's also a little bit about recursively walking directories and selectively looking for the files you want.

# Becoming the NSA of your Music
# ------------------------------
# Getting the metadata is incredibly easy. I'm only going to extract it from one artist today, but extending this out to covering your whole library is easy (well, as long as you store your music in one location and in a reasonable pattern).

# In[1]:

from tinytag import TinyTag
import os, os.path as path

# audio types TinyTag supports
valid_types = ('mp3', 'ogg', 'oga', 'wav', 'flac')

# artist directory
acid_bath = '/home/justanr/Music/Acid Bath/'

#extract the directories within the artist directory
albums = [path.join(acid_bath, a) for a in os.listdir(acid_bath) if not 'Demos' in a]

tracks = []

# extract tracks from each album directory
for album in albums:
    _tracks = []
    for t in os.listdir(album):
        # did you know it was possible to pass an iterable to str.endswith?
        if not t.endswith(valid_types):
            continue
        _tracks.append(path.join(album, t))
    tracks.extend(_tracks)

del _tracks # no need for hanger-ons.    

# convert track paths to TinyTag objects
tracks = [TinyTag.get(t) for t in tracks]

# string representation is actually a
# string representation of a dictionary
# created on the fly from the public
# values on the actual object
print(tracks[0])


# Out[1]:

#     {'track_total': '14', 'title': '\x03Jezebel', 'filesize': 11915076, 'artist': '\x03Acid Bath', 'album': '\x03When the Kite String Pops', 'track': '\x035', 'audio_offset': 192239, 'bitrate': 320.0, 'year': '1994', 'samplerate': 44100, 'duration': 297.87708785043435}
# 

# As an aside, if you've never listened to [Acid Bath](http://www.metal-archives.com/bands/Acid_Bath/19), I can't recommend them enough. Hard rocking, groovy sludgey metal with lyrics that are equal parts Lewis Carroll, grotesque and drug binge. Some songs are more the typical what the layman thinks of metal (Jezebel, Cheap Vodka) but with songs like Venus Blue, Bleed Me an Ocean and Dead Girl there's really something for most people.

# Data Munging and You
# --------------------
# Alright, looks like I have an encoding issue. There is something to note here though: `\x03` denotes `END OF TEXT` and to my understanding you're suppose to see it in ID3 tags (though, that's based on second hand information as my search-fu didn't turn up anything). However, I have actually run into an encoding issue using TinyTag (I'm not sure if the problem is with the file, Python, IPython or TinyTag). An example:

# In[2]:

nzp = TinyTag.get('/home/justanr/Music/At the Drive‐In/Relationship of Command/11 Non‐Zero Possibility.mp3')

print('Expected:      At the Drive-In - Relationship of Command - 11 - Non-Zero Possibility')
print('Actual:       ', ' - '.join([nzp.artist, nzp.album, nzp.track, nzp.title]))

# This is just a bandage.
# The actual issue is an encoding issue
# I've not been able to track down.

# I'd like to thank /u/anossov and /u/ryeguy146
# for help, even though we all agree this isn't
# the correct way to address the issue at hand

def fixer(value, ignore=(AttributeError, UnicodeEncodeError), handle=None):
    '''Actual fixer function for fix_track
    
    ignore is a tuple of exceptions we should just discard.
    handle is an optional exception handler.
    '''
    try:
        value = value.encode('latin-1').decode('utf-8').strip()
        # matching \x03 is frustrating
        # again, just a crutch to lean on
        if not value[0].isprintable():
            value = value[1:]
    except ignore as e:
        if handle:
            handle(e)
        else:
            pass
    finally:
        # we always end up here
        return value
    

def fix_track(
              track, 
              fixer=fixer, 
              fields=('artist', 'album', 'title', 'track', 'year', 'track_total'),
              int_convert=('track', 'year', 'track_total')
              ):
    '''Fix encoding issue encountered on some tracks.
    
    Accepts a track object and attempts to massage the data in our favor.
    * fixer is the function we want to run on this track to correct data
    * fields in the specific fields we'd like to attempt to correct
    * int_convert is a subset of fields that is data that should be integers
    '''
    for f in fields:
        value = getattr(track, f)
        if not value: 
            # value is likely None
            # we'll pass on this value
            # to avoid blowing up
            continue
        else:
            value = fixer(value)
        if f in int_convert:
            try:
                value = int(value)
            except ValueError:
                pass
        setattr(track, f, value)
        
    # TODO: need to make this mutable
    # for now, it's hardcoded as TinyTag
    # stores duration as a float
    track.duration = int(track.duration)
    
    # returning the track allows us
    # to be flexible in application
    # of this function
    return track

nzp = fix_track(nzp)
print('After Fixing: ', ' - '.join([nzp.artist, nzp.album, str(nzp.track), nzp.title]))
print(nzp)


# Out[2]:

#     Expected:      At the Drive-In - Relationship of Command - 11 - Non-Zero Possibility
#     Actual:        At the DriveâIn - Relationship of Command - 11 - NonâZero Possibility
#     After Fixing:  At the Drive‐In - Relationship of Command - 11 - Non‐Zero Possibility
#     {'track_total': 11, 'title': 'Non‐Zero Possibility', 'filesize': 5382993, 'artist': 'At the Drive‐In', 'album': 'Relationship of Command', 'track': 11, 'audio_offset': 2058, 'bitrate': 128.0, 'year': 2000, 'samplerate': 44100, 'duration': 336}
# 

# As you can see, encoding issues are *painful*. This bandage is the best I can come up with until I can actually track down and address the issue. However, this works *for now* (and like so many `#TODO: Address actual issue` functions, it'll inevitable end up in my codebase permanently).
# 
# This is an example of *data munging*. You'll mostly hear that phrase in machine learning and data processing. But when you think about, isn't all programming data processing? Data munging is the process of taking in data and massaging it into a form you can work with. Most of the time, this involves just converting data from one type to another. Sometimes it involves just throwing data away and knowing when you should.
# 
# In this case, it's taking a TinyTag object and breaking it into three separate pieces: Artist, Album and Track data models. Just like in the API data mocking post, these stand in for actual data models. However, now, there's a fair bit of magic going on: cacheing, auto registration of albums and tracks on relevant models, and for good measure: total ordering. 
# 
# Cacheing is not done entirely correctly, but do note the use of `WeakValueDictionary` which stores weak references. Weak references allow an object to be garbage collected when it's the only remaining reference left. Meaning if we created a bunch of Artist objects, stuffed them into permanent storage somewhere and then deleted the objects (and all their "strong" references), Python can come clean up some memory for us. Which is incredibly useful when dealing with a lot of data at once.

# In[3]:

import itertools as it
from functools import wraps, partial
from weakref import WeakValueDictionary

# Too lazy to spend time manipulating
# __new__ or making a metaclass 
# (actually, I spent a lot of time being frustrated at them)
# to handle this so there's this hack
def cache(cls):
    '''Helper caching and identification methods.'''
    _registry = WeakValueDictionary()
    _ids = it.count(1)
    
    def by_name(name):
        return _registry.get(name, None)
    
    @wraps(cls)
    def wrapper(name, *args, **kwargs):
        nonlocal _registry, _ids
        
        if name not in _registry:
            # create a new instance of the class
            instance = cls(name=name, *args, **kwargs)
            
            # generate id for the instance
            instance.id = next(_ids)
            
            # register the instance
            _registry[name] = instance
            
        #reuturn the instance
        return _registry[name]
    wrapper.by_name = by_name
    return wrapper
            
class ComparableMixin(object):
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __hash__(self):
        return hash(self._cmpkey())
        
    def __lt__(self, other):
        return self._compare(other, lambda s,o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s,o: s <= o)

    def __eq__(self, other):
       return self._compare(other, lambda s,o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s,o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s,o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s,o: s != o)
    
@cache
class Artist(ComparableMixin):
    def __init__(self, name, albums=None):
        self.id = None
        self.name = name
        # albums should be a list of albums
        # but it becomes a dictionary
        # probably shouldn't actually do this
        self.albums = albums or {}

        if self.albums:
            albums = [Album.by_name(a) for a in albums]
            self.albums = {a.name:a for a in albums if a is not None}
    
    def _cmpkey(self):
        '''This key is used by ComparableMixin for ordering.
        It is also used for hashing. Including the id is good
        practice here to ensure that we don't accidentally create
        two objects with the same name that makes this useless
        in a hashtable.
        '''
        
        # tuples compare across like this:
        # self[0] op other[0] ... self[n] op other[n]
        # until the tuples don't match
        # then Python sorts them accordingly
        # meaning often the whole tuple doesn't get
        # compared to another tuple
        # this is helpful when you want a default
        # multivalue sort
        return (self.name, self.id)
    
    def __repr__(self):
        return "<Artist name={} id={}>".format(self.name, self.id)

@cache
class Album(ComparableMixin):
    
    def __init__(self, name, artist=None, tracks=None):
        self.id = None
        self.name = name
        self.artist = Artist.by_name(artist)
        self.tracks = tracks or []
        
        if self.artist:
            self.artist.albums[self.name] = self
        
        if tracks:
            tracks = [Track.by_name(t) for t in tracks]
            self.tracks = [t for t in tracks if not t is None]
    
    def _cmpkey(self):
        return (self.artist, self.name, self.id)
    
    def __repr__(self):
        artist = self.artist.name if self.artist else "<BLANK>"
        return "<Album name={} artist={} id={}>".format(self.name, artist, self.id)

@cache
class Track(ComparableMixin):
    
    def __init__(self, name, track, length, artist=None, album=None):
        self.id = None
        self.name = name
        self.track = track
        self.length = length # in seconds
        self.artist = Artist.by_name(artist)
        self.album = Album.by_name(album)
        
        if self.album:
            self.album.tracks.append(self)

    def _cmpkey(self):
        return (self.album, self.track, self.name, self.id)

    def __repr__(self):
        album = self.album.name if self.album else "<BLANK>"
        artist = self.artist.name if self.artist else "<BLANK>"
        
        return "<Track artist={} album={} track={} name={} id={}>".format(artist, album, self.track, self.name, self.id)

# Mini unit tests ;)
# gorguts = Artist(name='Gorguts')
# obscura = Album(name='Obscura', artist='Gorguts')
# obscura_track = Track(name="Obscura", track=1, length=244, artist="Gorguts", album="Obscura")
# assert obscura.artist is gorguts
# assert obscura.name in gorguts.albums
# assert obscura_track in obscura.tracks
# assert obscura == gorguts.albums['Obscura']
# assert Artist.by_name('blank') is None
# assert Artist(name='test').id == 2
# assert Artist(name='Gorguts') is gorguts
# print(gorguts, obscura, obscura_track)


# So much hard work taken care of for us with a little magic. The little unittest at the end is to assure us everything is working as intended. Uncomment them to see them in action. 
# 
# The `Comparable` mixin, I shamelessly [stole](http://regebro.wordpress.com/2010/12/13/python-implementing-rich-comparison-the-correct-way/), but it'll make life much easier on the other end of this conversion if we need to sort a collection of `Artist`, `Album` or `Track` objects. I added the `__hash__` method to it. Technically it should be a `HashableMixin`, there's already a *ton* of stuff going on in this frame, I decided another class would just add to the noise.
# 
# Now, we need to massage our list of Acid Bath tracks into these models. You didn't think I forgot about them, did you?

# In[4]:

from collections import namedtuple

tracks = [fix_track(track) for track in tracks]

# our sort and groupby key function
key = namedtuple('key', ['artist', 'album', 'track'])
compare = lambda t: key(t.artist, t.album, t.track)

# named after the pattern
adaptor = lambda t: {'artist':t.artist, 'album':t.album, 'length':t.duration, 'name':t.title, 'track':t.track}

tracks.sort(key=compare)

# this keeps us from creating a big list
# with the same artist, albums and tracks
# over and over by accident
artists = set()
albums  = set()
_tracks = set()

for keys, grouped in it.groupby(tracks, key=compare):
    artists.add(Artist(name=keys.artist))
    albums.add(Album(name=keys.album, artist=keys.artist))
    for track in grouped:
        _tracks.add(Track(**adaptor(track)))

artists = list(artists)
albums  = list(albums)
tracks  = list(_tracks)

# no hanger ons!
del _tracks

print("Artists: ", *artists, sep='\n')
print("\nAlbums: ", *sorted(albums), sep='\n')
print("\nTracks: ", *sorted(tracks), sep='\n')


# Out[4]:

#     Artists: 
#     <Artist name=Acid Bath id=1>
#     
#     Albums: 
#     <Album name=Paegan Terrorism Tactics artist=Acid Bath id=1>
#     <Album name=When the Kite String Pops artist=Acid Bath id=2>
#     
#     Tracks: 
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=1 name=Paegan Love Song id=1>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=2 name=Bleed Me an Ocean id=2>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=3 name=Graveflower id=3>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=4 name=Diäb Soulé id=4>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=5 name=Locust Spawning id=5>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=6 name=Old Skin id=6>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=7 name=New Death Sensation id=7>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=8 name=Venus Blue id=8>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=9 name=13 Fingers id=9>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=10 name=New Corpse id=10>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=11 name=Dead Girl id=11>
#     <Track artist=Acid Bath album=Paegan Terrorism Tactics track=12 name=Ode of the Peagan id=12>
#     <Track artist=Acid Bath album=When the Kite String Pops track=1 name=The Blue id=13>
#     <Track artist=Acid Bath album=When the Kite String Pops track=2 name=Tranquilized id=14>
#     <Track artist=Acid Bath album=When the Kite String Pops track=3 name=Cheap Vodka id=15>
#     <Track artist=Acid Bath album=When the Kite String Pops track=4 name=Finger Paintings of the Insane id=16>
#     <Track artist=Acid Bath album=When the Kite String Pops track=5 name=Jezebel id=17>
#     <Track artist=Acid Bath album=When the Kite String Pops track=6 name=Scream of the Butterfly id=18>
#     <Track artist=Acid Bath album=When the Kite String Pops track=7 name=Dr. Seuss Is Dead id=19>
#     <Track artist=Acid Bath album=When the Kite String Pops track=8 name=Dope Fiend id=20>
#     <Track artist=Acid Bath album=When the Kite String Pops track=9 name=Toubabo Koomi id=21>
#     <Track artist=Acid Bath album=When the Kite String Pops track=10 name=God Machine id=22>
#     <Track artist=Acid Bath album=When the Kite String Pops track=11 name=The Morticians Flame id=23>
#     <Track artist=Acid Bath album=When the Kite String Pops track=12 name=What Color Is Death id=24>
#     <Track artist=Acid Bath album=When the Kite String Pops track=13 name=The Bones of Baby Dolls id=25>
#     <Track artist=Acid Bath album=When the Kite String Pops track=14 name=Cassie Eats Cockroaches id=26>
# 

# Of course to avoid dealing with "hanger on" variables as I like to call them, this logic (as well as the logic to take a directory and extract it's subdirectories and finally the music files in it) could be stored in a function that'd be callable again and again. Something like this:

# In[5]:

def get_music_files(basedir, valid_types=('mp3', 'ogg', 'oga', 'wav', 'flac'), ignore=None):
    '''Walks the base directory to extract album directories from it. 
    Then walks each album directory to extract valid audio files from it.
    
    The optional ignore attribute is a callback that allows you to dynamically
    ignore certain directories.
    '''
    
    tracks = []
    albums = []
    
    for a in os.listdir(basedir):
        if ignore and ignore(a):
            continue
        albums.append(path.join(basedir, a))
    
    for album in albums:
        _tracks = []
        for t in os.listdir(album):
            if not t.endswith(valid_types):
                continue
            _tracks.append(path.join(album, t))
        tracks.extend(_tracks)
        
    return tracks

def convert_tinytags(tracks, key_fields=('artist', 'album', 'track'), adaptor=None):
    '''Accepts an iterable of TinyTag objects (or similar) and parses them
    into Artist, Album and Track objects.
    
    * tracks: iterable of track objects
    * key fields: fields used for sorting and grouping the track objects
    * adaptor: optional callback for extracting information from the old
        track objects to create the new track objects
    '''
    
    key = namedtuple('key', key_fields)
    
    def compare(track):
        values = []
        for field in key_fields:
            values.append(getattr(track, field))
        return key(*values)
    
    if not adaptor:
        adaptor = lambda t: {'artist':t.artist, 'album':t.album, 'length':t.duration, 'name':t.title, 'track':t.track}
    
    tracks.sort(key=compare)
    
    # this keeps us from creating a big list
    # with the same artist and albums over and over
    artists = set()
    albums  = set()
    _tracks = set()
    
    for keys, grouped in it.groupby(tracks, key=compare):
        artists.add(Artist(name=keys.artist))
        albums.add(Album(name=keys.album, artist=keys.artist))
        for track in grouped:
            _tracks.add(Track(**adaptor(track)))

    return list(artists), list(albums), list(_tracks)

tracks = get_music_files('/home/justanr/Music/At the Drive‐In/')
tracks = [TinyTag.get(t) for t in tracks]
tracks = list(map(fix_track, tracks))
artists, albums, tracks = convert_tinytags(tracks)

# of course you could just:
# artists, albums, tracks = convert_tinytags([fix_track(TinyTag.get(t)) for t in get_music_files(...)])
# But that's also pretty hard to read, too

print("Artists: ", *artists, sep='\n')
print("\nAlbums: ", *sorted(albums), sep='\n')
print("\nTracks: ", *sorted(tracks), sep='\n')


# Out[5]:

#     Artists: 
#     <Artist name=At the Drive‐In id=2>
#     
#     Albums: 
#     <Album name=Relationship of Command artist=At the Drive‐In id=3>
#     <Album name=Vaya artist=At the Drive‐In id=4>
#     
#     Tracks: 
#     <Track artist=At the Drive‐In album=Relationship of Command track=1 name=Arcarsenal id=27>
#     <Track artist=At the Drive‐In album=Relationship of Command track=2 name=Pattern Against User id=28>
#     <Track artist=At the Drive‐In album=Relationship of Command track=3 name=One Armed Scissor id=29>
#     <Track artist=At the Drive‐In album=Relationship of Command track=4 name=Sleepwalk Capsules id=30>
#     <Track artist=At the Drive‐In album=Relationship of Command track=5 name=Invalid Litter Dept. id=31>
#     <Track artist=At the Drive‐In album=Relationship of Command track=6 name=Mannequin Republic id=32>
#     <Track artist=At the Drive‐In album=Relationship of Command track=7 name=Enfilade id=33>
#     <Track artist=At the Drive‐In album=Relationship of Command track=8 name=Rolodex Propaganda id=34>
#     <Track artist=At the Drive‐In album=Relationship of Command track=9 name=Quarantined id=35>
#     <Track artist=At the Drive‐In album=Relationship of Command track=10 name=Cosmonaut id=36>
#     <Track artist=At the Drive‐In album=Relationship of Command track=11 name=Non‐Zero Possibility id=37>
#     <Track artist=At the Drive‐In album=Vaya track=1 name=Rascuache id=38>
#     <Track artist=At the Drive‐In album=Vaya track=2 name=Proxima Centauri id=39>
#     <Track artist=At the Drive‐In album=Vaya track=3 name=Ursa Minor id=40>
#     <Track artist=At the Drive‐In album=Vaya track=4 name=Heliotrope id=41>
#     <Track artist=At the Drive‐In album=Vaya track=5 name=Metronome Arthritis id=42>
#     <Track artist=At the Drive‐In album=Vaya track=6 name=300 MHz id=43>
#     <Track artist=At the Drive‐In album=Vaya track=7 name=198d id=44>
# 

# Of course, we could generalize `get_music_files` to recursively walk the base Music directory so it's not confined to my organizational scheme.

# In[6]:

def r_get_music_files(basedir, valid_types=('mp3', 'ogg', 'oga', 'wav', 'flac'), ignore=None):
    tracks = []

    for f in os.listdir(basedir):
        f = path.join(basedir, f)
        # we can now filter both directories and files
        # passing the full path will even allow
        # ignore to filter based on if `f` is
        # a directory or file
        if ignore and ignore(f):
            continue
        elif path.isdir(f):
            tracks.extend(r_get_music_files(f, valid_types, ignore))
        elif not f.endswith(valid_types):
            continue
        else:
            # must be a file we're looking for
            tracks.append(f)
    
    return tracks

# only going to point this at a artist directory
# the `An Awesome Wave` album is a directory in here
# just to demonstrate that this does in fact work as intended
tracks = r_get_music_files('/home/justanr/Music/Alt-J/')
tracks = [TinyTag.get(t) for t in tracks]
tracks = list(map(fix_track, tracks))
artists, albums, tracks = convert_tinytags(tracks)

print("Artists: ", *artists, sep='\n')
print("\nAlbums: ", *sorted(albums), sep='\n')
print("\nTracks: ", *sorted(tracks), sep='\n')


# Out[6]:

#     Artists: 
#     <Artist name=Alt-J id=3>
#     
#     Albums: 
#     <Album name=An Awesome Wave artist=Alt-J id=5>
#     
#     Tracks: 
#     <Track artist=Alt-J album=An Awesome Wave track=1 name=Intro id=45>
#     <Track artist=Alt-J album=An Awesome Wave track=2 name=Intrelude 1 id=46>
#     <Track artist=Alt-J album=An Awesome Wave track=3 name=Tesselate id=47>
#     <Track artist=Alt-J album=An Awesome Wave track=4 name=Breezeblocks id=48>
#     <Track artist=Alt-J album=An Awesome Wave track=5 name=Interlude 2 id=49>
#     <Track artist=Alt-J album=An Awesome Wave track=6 name=Something Good id=50>
#     <Track artist=Alt-J album=An Awesome Wave track=7 name=Disolve Me id=51>
#     <Track artist=Alt-J album=An Awesome Wave track=8 name=Matilda id=52>
#     <Track artist=Alt-J album=An Awesome Wave track=9 name=Ms id=53>
#     <Track artist=Alt-J album=An Awesome Wave track=10 name=Fitzpleasure id=54>
#     <Track artist=Alt-J album=An Awesome Wave track=11 name=Interlude 3 id=55>
#     <Track artist=Alt-J album=An Awesome Wave track=12 name=Bloodflow id=56>
#     <Track artist=Alt-J album=An Awesome Wave track=13 name=Taro id=57>
# 

# That works, but it's recursive (in a bad way). And it stores everything *in memory*. Yuck. I have approximately 26,000 or so audio files chilling in my music directory. Do we really want to store all that information all at once when the ultimate goal is to simlply stuff it in the database (did I give away my plan?) and throw the immediate result away.
# 
# You know what's really good at doing something and then throwing results away? Generators. Adapting `r_get_music_files` to a general file walker is trivial but I'm slightly vain and overly happy with my end generator. Before anyone jumps on me and says, "ALEC! There's os.walk! You've got os imported already!" 
# 
# I know. `os.walk` almost does what we want: start with a folder, find the subfolders, yield a list of things. Except in this case it's three tuples: `(dirpath, dirnames, filenames)`. Which means we need to then parse that before getting to what we want. We could also use glob for this -- iglob uses an iterator -- but that delves into using regular expressions. There's `pathlib` in 3.4, but I'm ultimately unfamilar with it.

# In[7]:

def walk(basedir, ignore=None):
    for f in sorted(os.listdir(basedir)):
        # store fullpath separately so we can
        # easily pass it if needed
        fp = os.path.join(basedir, f)
        if ignore and ignore(basedir, f):
            continue
        elif os.path.isdir(fp):
            # to quote Dave Beazley:
            # "Yield from is the ultimate not my problem.
            # It just says, 'Here's some generator, you deal with it.'"
            yield from walk(fp, ignore)
        else:
            # must be a file we're looking for
            yield fp

def ignore(base, f, valid_types=('.mp3', '.ogg', '.oga', '.wav', '.flac')):
    '''Example ignore function.'''
    fp = os.path.join(base, f)
    # ignore 'hidden' files and directories
    if f.startswith('.'):
        return True
    # filter actual files based on their extension
    elif os.path.isfile(fp) and not f.lower().endswith(valid_types):
        return True
    # got here, so we return False to *not* ignore this file
    # a little confusing
    # also, I don't like if/elif without a else
    else:
        return False

# breaking the adaptor fully out into it's own function as well
# even though for this example we're dealing exclusively with
# TinyTag, I did give links to several other metadata libraries
# maybe you're dealing with one of those?
adaptor = lambda t: {'artist':t.artist, 'album':t.album, 'length':t.duration, 'name':t.title, 'track':t.track}

def convert_track(track, adaptor):
    info = adaptor(track)
    artist = Artist(name=info['artist'])
    album = Album(name=info['album'], artist=info['artist'])
    track = Track(**info)
    return artist, album, track

get_ipython().magic("timeit -n 100 -r 5 next(walk('/home/justanr/Music/', ignore=ignore))")
get_ipython().magic("timeit -n 100 -r 5 next(os.walk('/home/justanr/Music'))")
track = next(walk('/home/justanr/Music/', ignore=ignore))
track = TinyTag.get(track)
track = fix_track(track)
print(*convert_track(track, adaptor), sep='\n')


# Out[7]:

#     100 loops, best of 5: 295 µs per loop
#     100 loops, best of 5: 1.34 ms per loop
#     <Artist name=16 id=4>
#     <Album name=Bridges to Burn artist=16 id=6>
#     <Track artist=16 album=Bridges to Burn track=1 name=Throw in the Towel id=58>
# 

# It's still procedural code but it's nicely composable. And it's quick. In this particular instance, it's faster than os.walk but I've always thought benchmarks are useless without a greater context -- so for shits and giggles, I ran both over my Music directory (with all 26,000+ files), just spitting values into 0 length deque, and my walk function took about ~560ms, os.walk took ~350ms. Considering we're doing a little more work than os.walk, I'll take it any day of the week.
# 
# And even though convert_track only accepts one track now, chunking over walk with `islice` is obvious.
# 
# Now that I've digressed completely from audio metadata to quickly processing through files, I think I'll end here.
