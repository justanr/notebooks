
# Building Restful APIs can be hard. But with Flask and a few extensions, they don't need to be. For this brief tutorial, you'll need to install:
# 
# * [Flask](http://flask.pocoo.org/docs/0.10/)
# * [Flask-Restful](http://flask-restful.readthedocs.org/en/latest/)
# * [Flask-Marshmallow](http://flask-marshmallow.readthedocs.org/en/latest/)
# 
# All of these are available on PyPI and ergo `pip` (and `easy_install` if that's your jam instead).
# 
# Okay, someone's looking at me confused right now because [Marshmallow](http://marshmallow.readthedocs.org/en/latest/) and Restful overlap in the marshalling department. I prefer Marshmallow's powerful serializing abilities to, in my opinion, Restful's more limited approach. Why Flask-Marshmallow? It can introspect endpoints and dynamically create links.
# 
# You'll notice that there's no database required for this, that's because we're focusing on *building the API* rather than where the data comes from. I'll also admit, there's quite a bit of repeated code in here, again the focus was on the API, not the other parts.

# Setup
# -----
# First, we'll have to setup the app and the two extensions.

# In[ ]:

from flask import Flask
from flask.ext.restful import Api, Resource
from flask.ext.marshmallow import Marshmallow

app = Flask(__name__)
api = Api(app)
ma = Marshmallow(app)


# Data Source
# -----------
# First, our data source. I'm using basic objects here simply to not worry about connecting to any external sources. There are three:
# 
# * Artist
# * Album
# * Track
# 
# We're going to model a basic music system (as in, extremely basic). The objects themselves are extremely basic and essentially just dictionaries in this case, but they're standing in for actual data models (say, for SQLAlchemy). They're circularly linked, such that:
# 
#     >>> artist = artists[0]
#     >>> artist.albums[0].artist is artist
#     ... True
#     >>> artist.albums[0].tracks[0].artist is artist
#     ... True
#     
# And so on with the albums and tracks. However, since we're managing these by hands...it isn't much fun.

# In[ ]:

class Artist(object):
    def __init__(self, id, name, albums=None):
        self.id = id
        self.name = name
        self.albums = albums or []

class Album(object):
    def __init__(self, id, name, artist=None, tracks=None):
        self.id = id
        self.name = name
        self.artist = artist
        self.tracks = tracks or []

class Track(object):
    def __init__(self, id, name, position, length, artist=None, albums=None):
        self.id = id
        self.name = name
        self.length = length # length in seconds
        self.position = position
        self.artist = artist
        self.albums = albums or [] # tracks can appear on multiple albums


# Flask-Marshmallow
# -----------------
# Setting up serializers with Marshmallow and it's Flask extension is a breeze and an absolute joy. Don't consider this a *tour de force* but as a short introduction to the main features of them.
# 
# ###diff Marshmallow Flask-Marshmallow
# The biggest change to Flask-Marshmallow is that all the fields are built into your Flask-Marshmallow object. Before you had to use `from marshmallow import Serializer, fields`. Flask-Marshmallow also adds a URL field and a helper method for building a collection of links.
# 
# So, let's set them up.

# In[ ]:

class ArtistSerializer(ma.Serializer):
    albums = ma.Nested('AlbumSerializer', exclude=('artist',), many=True)
    
    _links = ma.Hyperlinks({
        'self':ma.URL('artist', id='<id>'),
        'collection':ma.URL('artists')
        })
    
    class Meta:
        additional = ('id', 'name')

class AlbumSerializer(ma.Serializer):
    artist = ma.Nested('ArtistSerializer', exclude=('albums',))
    tracks = ma.Nested('TrackSerializer', exclude=('albums', 'artist'), many=True)
    
    _links = ma.Hyperlinks({
        'self':ma.URL('album', id='<id>'),
        'collection':ma.URL('albums')
        })
    
    class Meta:
        additional = ('id', 'name')

class TrackSerializer(ma.Serializer):
        albums = ma.Nested('AlbumSerializer', exclude=('artist', 'tracks'), many=True)
        artist = ma.Nested('ArtistSerializer', exclude=('albums'))
        length = ma.Method('convert_time')
        
        _links = ma.Hyperlinks({
            'self':ma.URL('track', id='<id>'),
            'collection':ma.URL('tracks')
            })
        
        def convert_time(self, track):
            seconds = track.length
            mins = seconds//60
            seconds -= (mins*60)
            
            return "{!s:2>0}:{!s:2>0}".format(mins, seconds)
        
        class Meta:
            addition = ('id', 'name', 'position')


# Just to briefly go over this:
# 
# * Serializers subclass the main `ma.Serializer` class where the actual magic happens. All we're concerned about is telling it which fields it should look for and where it's at.
# * `ma.Nested` allows you to nest serializer by either passing in a class *or* in >= 0.6.0 you can pass in the name of the serializer, which is also the greatest thing ever because before you had to define your base serializers and then subclass them to add in any nested serializers that are defined afterwards. The `many` keyword tells the serializer to expect an iterable and run the nested serializer over all the items in it.
# * `ma.Method` runs a method in the serializer and passes it the object it's attempting to serialize into it
# * `ma.Hyperlinks` is like a serializer itself in that it'll accept a dictionary of fields and introspect it to output data.
# * `ma.URL` is like `Flask.url_for` in that'll it accepts an endpoint and any arguments for the endpoint to create a url for it.
# * The `class Meta` definition in those classes is actually a shortcut for properties that Marshmallow can automatically marshal. Artist.Meta is essentially a short cut for:
#     * `id = ma.Integer('id')`
#     * `name = ma.String('name')`
# * Serializers themselves are used via: `MySerializer(myobject)` or `MySerializer([myobject, myobject2], many=True)` The new object has one property that we're interested in: `Serializer.data` which returns an OrderedDict of all the fields processed
# 
# 
# Doing this with Flask-Restful is not as easy or as much fun... Restful's serializers are stores in dictionaries rather than in a custom container.

# In[ ]:

from flask.ext.restful import fields, marshal, marshal_with

class HumanReadableTime(fields.Raw):
    def format(self, value):
        mins = value//60
        seconds -= (mins*60)
        return "{!s:2>0}:{!s:2>0}".format(mins, seconds)

artist_fields = {'name':fields.String, 'id':fields.Integer}
album_fields = {'name':fields.String, 'id':fields.Integer}
track_fields = {
    'name':fields.String, 'id':fields.Integer, 'position':fields.Integer,
    'length':HumanReadableTime, 'artist':fields.Nested(artist_fields),
    'albums':fields.List(album_fields)
    }


# Nesting structures is similar to Marshmallow except there's no option to exclude fields, which leads to painful tricks like creating dictionaries on the fly or absuing ChainMap. This quickly spirals out of control. All to avoid recursively serialization. Whereas with Marshmallow's serializers it's as easy as passing in the fields you want to exclude.

# Let's build some data, by hand, to throw at our serializers. I'm a big fan of death metal, especially the stranger, dissonant corners of it. However, feel free to sub in any other bands, albums and tracks you like.

# In[ ]:

from itertools import chain

immolation = Artist(id=1, name='Immolation')
gorguts = Artist(id=2, name='Gorguts')
ulcerate = Artist(id=3, name='Ulcerate')

artists = [immolation, gorguts, ulcerate]

ctawb = Album(id=1, name='Closer to a World Below', artist=immolation)
majesty_and_decay = Album(id=2, name='Majesty and Decay', artist=immolation)
obscura = Album(id=3, name='Obscura', artist=gorguts)
eif = Album(id=4, name='Everything is Fire', artist=ulcerate)

immolation.albums.extend([ctawb, majesty_and_decay])
gorguts.albums.append(obscura)
ulcerate.albums.append(eif)

albums = [ctawb, majesty_and_decay, obscura, eif]

def build_tracks(tracks, artist, albums, offset=0):
    '''Accepts an iterable of track parts to construct track objects 
    and then attaches the tracklist to each album passed to the function.
    '''
    
    tracks = [Track(
        id=i+offset+1, position=i+1, artist=artist, albums=albums,
        name=t[0], length=t[1]
        ) for i, t in enumerate(tracks)]
    
    for a in albums:
        a.tracks.extend(tracks)

        
offset = 0

ctawb_tracks = [
    ('Higher, Coward', 300), ('Father, You\'re Not a Father', 303),
    ('Furthest From the Truth', 266), ('Fall From a High Place', 277),
    ('Unpardonable Sin', 473), ('Lost Passion', 340),                           
    ('Put My Hand in the Fire', 252), ('Close to a World Below', 499)
    ]
build_tracks(ctawb_tracks, artist=immolation, albums=[ctawb], offset=offset)

offset += len(ctawb_tracks)
mad_tracks = [
    ('Intro', 79), ('The Purge', 199), ('A Token of Malice', 161),
    ('Majesty and Decay', 269), ('Divine Code', 219), ('The Human Form', 244),
    ('A Glorious Epoch', 278), ('Interlude', 124),
    ('A Thunderous Consequence', 239), ('The Rapture of Ghosts', 519),
    ('Power and Shame', 224), ('The Comfort of Cowards', 552)
    ]
build_tracks(mad_tracks, artist=immolation, albums=[majesty_and_decay], offset=offset)

offset += len(mad_tracks)
obscura_tracks = [
    ('Obscura', 244), ('Earthly Love', 244), ('The Carnal State', 188),
    ('Nostalgia', 370), ('The Art of Somber Ecstasy', 260),
    ('Clouded', 572), ('Subtle Body', 203), ('Rapturous Grief', 327),           
    ('La Vie Est Prelud... (La Morte Orgasme)', 208),
    ('Illuminatus', 375), ('Faceless Ones', 230), ('Sweet Silence', 405)
    ]

offset += len(obscura_tracks)
eif_tracks = [
    ('Drown Within', 402), ('We are Nil', 541), ('Withered and Obsolete', 370),
    ('Caecus', 386), ('Tyranny', 522), ('The Earth at Its Knees', 545),
    ('Soulessness Embraced', 366), ('Everything is Fire', 472)
    ]
build_tracks(eif_tracks, artist=ulcerate, albums=[eif], offset=offset)

tracks = list(chain.from_iterable(a.tracks for a in albums))


# Holy crap that's a lot of hassle to go through just to mockup some data. But, it's there. How do the serializers handle?

# In[ ]:

ArtistSerialize(immolation, exclude=('albums',).data


#     {
#         "artist": {
#             "_links": {
#                 "collection": "/artist/",
#                 "self": "/artist/1/"
#             },
#             "id": 1,
#             "name": "Immolation"
#         }
#     }

# In[ ]:

TrackSerialize(tracks[:2], many=True).data


#     {
#         "tracks": [
#             {
#                 "_links": {
#                     "collection": "/track/",
#                     "self": "/track/1/"
#                 },
#                 "albums": [
#                     {
#                         "_links": {
#                             "collection": "/album/",
#                             "self": "/album/1/"
#                         },
#                         "id": 1,
#                         "name": "Closer to a World Below"
#                     }
#                 ],
#                 "artist": {
#                     "_links": {
#                         "collection": "/artist/",
#                         "self": "/artist/1/"
#                     },
#                     "id": 1,
#                     "name": "Immolation"
#                 },
#                 "id": 1,
#                 "length": "05:00",
#                 "name": "Higher, Coward",
#                 "position": 1
#             },
#             {
#                 "_links": {
#                     "collection": "/track/",
#                     "self": "/track/2/"
#                 },
#                 "albums": [
#                     {
#                         "_links": {
#                             "collection": "/album/",
#                             "self": "/album/1/"
#                         },
#                         "id": 1,
#                         "name": "Closer to a World Below"
#                     }
#                 ],
#                 "artist": {
#                     "_links": {
#                         "collection": "/artist/",
#                         "self": "/artist/1/"
#                     },
#                     "id": 1,
#                     "name": "Immolation"
#                 },
#                 "id": 2,
#                 "length": "05:03",
#                 "name": "Father, You're Not a Father",
#                 "position": 2
#             }
#         ]
#     }

# API Endpoints
# -------------
# Flask-RESTful makes building an API stupid easy. It does almost all the hardwork for you, leaving you to deal with just the implementation details of the API. However, this example won't be showing off the niceties of Flask-RESTful as the API endpoints just implement a GET HTTP method. I'll save the others for a later example.

# In[ ]:

class SingleArtist(Resource):
    def get(self, id):
        return {'artist':ArtistSerializer(artists[id-1]).data}

class SingleAlbum(Resource):
    def get(self, id):
        return {'album':AlbumSerializer(albums[id-1]).data}

class SingleTrack(Resource):
    def get(self, id):
        return {'track':TrackSerializer(tracks[id-1]).data}

class ListArtist(Resource):
    def get(self):
        return {'artists':ArtistSerializer(artists, many=True).data}

class ListAlbum(Resource):
    def get(self):
        return {'albums':AlbumSerializer(albums, many=True).data}

class ListTrack(Resource):
    def get(self):
        return {'tracks':TrackSerializer(tracks, many=True).data}

api.add_resource(SingleArtist, '/artist/<int:id>/', endpoint='artist')
api.add_resource(ListArtist, '/artist/', endpoint='artists')

api.add_resource(SingleAlbum, '/album/<int:id>/', endpoint='album')
api.add_resource(ListAlbum, '/album/', endpoint='albums')

api.add_resource(SingleTrack, '/track/<int:id>/', endpoint='track')
api.add_resource(ListTrack, '/track/', endpoint='tracks')


# That's It.
# ----------
# After all this is to run your app somewhere. Either when the script is `__main__` or importing the app into another script to run it. Have fun, play with it, modify it and see what you can get it to do.
