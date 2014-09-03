
# API V2: SQLAlchemy Boogaloo
# ---------------------------
# Now that we have our skeleton API built and we can pull the metadata out of MP3 files, we can build an actual data driven API instead of processing everything by hand.
# 
# ###Tools needed
# 
# * Flask
# * SQLAlchemy
# * MutagenX (Or Mutagen if you're running Python2)
# * Flask-Restful
# * Flask-Marshmallow
# * Flask-Script (working on replacing this with [Click](http://click.pocoo.org/3/))
# 
# Why no TinyTag? I let TinyTag go after figuring out that the encoding error is centered there. Originally, I had not used Mutagen because it had given me issues. Turns out Mutagen supports Python2. There's a fork -- MutagenX -- that supports Python3. Problem solved.

# Setup
# -----
# Setting up the data driven API is pretty straight forward. However, I'm going to touch on a few more advanced things in here because simply doing an incremental development blog post would be terribly boring to me. The first slightly advanced thing is going to be modularizing the Flask app. Here's what my directory layout looks like right now:
# 
#     FlaskAmp/
#     ├── app
#     │   ├── config.py
#     │   ├── dev-sqlite.db
#     │   ├── factory.py
#     │   ├── __init__.py
#     │   ├── models.py
#     │   ├── serializers.py
#     │   └── utils.py
#     ├── LICENSE
#     ├── manager.py
#     ├── README.md
#     └── requirements
# 
# It's a pretty standard layout. But it bears repeating. Under the `app` directory is where our action takes place. We'll go over each of these files.

# In[ ]:

#app/models.py
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, unique=True)
    albums = db.relationship('Album', backref=db.backref('artist', uselist=False), order_by='Album.name')
    tracks = db.relationship('Track', backref=db.backref('artist', uselist=False), lazy='noload')

class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, unique=True)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'))
    tracks = db.relationship(
        'Track', backref=db.backref('album', uselist=False),
        lazy='immediate', order_by='Track.position')
    
class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, primary_key=True)
    length = db.Column('length', db.Integer)
    position = db.Column('position', db.Integer)
    location = db.Column('location', db.Unicode)
    stream = db.Column('stream', db.String)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'))
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('albums.id'))


# This is a pretty standard setup for Flask-SQLAlchemy models. The only thing most people might not be familar with is the `lazy='noload'` on the relationship from Artist to Track. This tell SQLAlchemy to *never* load this data. Why? For now, we're not interested in loading it. Given that I'm already working on a much more indepth model structure, this'll get changed in the future.

# In[ ]:

#app/serializers.py
#this is pretty similar to before
from flask.ext.marshmallow import Marshmallow

ma = Marshmallow()

class ArtistSerializer(ma.Serializer):
    albums = ma.Nested('AlbumSerializer', exclude=('artist',), many=True)
    
    _links = ma.Hyperlinks({
        'self':ma.URL('artist', id='<id>'),
        'collection':ma.URL('artist')
        })
    
    class Meta:
        fields = ('id', 'name', 'albums', 'links')

class AlbumSerializer(ma.Serializer):
    artist = ma.Nested('ArtistSerializer', exclude=('albums',))
    tracks = ma.Nested('TrackSerializer', exclude=('albums', 'artist'), many=True)
    
    _links = ma.Hyperlinks({
        'self':ma.URL('album', id='<id>'),
        'collection':ma.URL('album')
        })
    
    class Meta:
        fields = ('id', 'name', 'artist', 'tracks', 'links')

class TrackSerializer(ma.Serializer):
        albums = ma.Nested('AlbumSerializer', exclude=('artist', 'tracks'), many=True)
        artist = ma.Nested('ArtistSerializer', exclude=('album'))
        length = ma.Method('convert_time')
        
        _links = ma.Hyperlinks({
            'self':ma.URL('track', id='<id>'),
            'collection':ma.URL('track')
            })
        
        def convert_time(self, track):
            seconds = track.length
            mins = seconds//60
            seconds -= (mins*60)
            
            return "{!s:2>0}:{!s:2>0}".format(mins, seconds)
        
        class Meta:
            fields = ('id', 'artist', 'album', 'name', 'position', 'length', 'links', 'stream')


# The only thing I'll note here is the use of `Meta.fields` rather than additional and that we're only exposing the streaming id for tracks to the serializer (and thus through the API) instead of both it *and* the file location. Giving away information like a file structure just makes it easier for people with malicious intent to gain access to the system.

# In[ ]:

#app/config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = False
    
    @staticmethod
    def init_app(app):
        pass

class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV-DATABASE-URI') or 'sqlite:///{}'.format(os.path.join(basedir, 'dev-sqlite.db'))

configs = {
    'dev' : DevConfig,
    'default' : DevConfig
    }


# In[ ]:

#app/factory.py
from flask import Flask
from .config import configs

def create_app(env, exts=()):
    app = Flask(__name__)
    config = configs.get(env, 'default')
    app.config.from_object(config)
    config.init_app(app)
    
    for ext in exts:
        ext.init_app(app)
    
    return app


# You'll see a lot of people turning to a factory for creating their application. However, they'll explicitly initialize their extensions one at a time. In this case, we pass in an environment and a list of extensions to initialize instead. I find that this is a little more flexible and doesn't rely on abusing scoping in Python.

# In[ ]:

#app/__init__.py
from flask import request, abort, send_file
from flask.ext.restful import Api, Resource
from .models import Artist, Album, Track
from .serializers import ArtistSerializer, AlbumSerializer, TrackSerializer
from .factory import create_app

app = create_app('dev', exts=[ma,db])
api = Api(app) # I've had strange things happen initializing the Restful API afterwards...

class SingleArtist(Resource):
    def get(self, id):
        artist = Artist.query.get_or_404(id)
        return {'artist' : ArtistSerializer(artist)}

class SingleAlbum(Resource):
    def get(self, id):
        album = Album.query.get_or_404(id)
        return {'album' : AlbumSerializer(artist)}

class SingleTrack(Resource):
    def get(self, id):
        track = Track.query.get_or_404(id)
        return {'track' : TrackSerializer(artist)}

class ListArtist(Resource):
    def get(self):
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        
        q = Artist.query.order_by(Artist.name)
        q = q.paginate(page, limit, error_out=False)
        
        return {'artists' : ArtistSerializer(q.items, many=True)}

class ListAlbum(Resource):
    def get(self):
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        
        q = Album.query.join(Artist).filter(Artist.id==Album.artist_id)
        q = q.order_by(Artist.name, Album.name)
        q = q.paginate(page, limit, error_out=False)
        
        return {'artists' : AlbumSerializer(q.items, many=True)}

class ListTrack(Resource):
    def get(self):
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        
        q = Track.query.join(Artist, Album)
        q = q.filter(Artist.id==Album.artist_id, Album.id==Track.album_id)
        q = q.order_by(Artist.name, Album.name, Track.position)
        q = q.paginate(page, limit, error_out=False)
        
        return {'artists' : TrackSerializer(q.items, many=True)}

@app.route('/stream/<stream_id>/', methods=['GET'])
def stream(stream_id):
    track = Track.query.filter(Track.stream==stream_id).first()
    if not track:
        abort(404)
    
    return send_file(track.location)
    
api.add_resource(SingleArtist, '/artist/<int:id>/', endpoint='artist')
api.add_resource(ListArtist, '/artist/', endpoint='artists')

api.add_resource(SingleAlbum, '/album/<int:id>/', endpoint='album')
api.add_resource(ListAlbum, '/album/', endpoint='albums')

api.add_resource(SingleTrack, '/track/<int:id>/', endpoint='track')
api.add_resource(ListTrack, '/track/', endpoint='tracks')


# There's a few differences here. I'll address a few:
# 
# * Flask-SQLAlchemy provides a custom query object which locates our session for us. So, unlike regular SQLAlchemy, we don't have to directly use the session object. This can make querying feel a little odd if you're not used to it but ultimately, it acts the same.
# * When joining two models in SQLAlchemy, you need to explicitly filter on the join you'd like. There's multiple ways of doing this. I'll leave the others as an exercise to the reader.
# * Flask-SQLAlchemy includes a pagination helper object. It allows you to specify just a page and limit and `paginate` will return several [helpful bits](https://pythonhosted.org/Flask-SQLAlchemy/api.html#flask.ext.sqlalchemy.Pagination) such as `has_next`, `has_prev`, `next_num` and `prev_num` among others.
# * `abort` allows you to redirect to an error page. Flask-SQLAlchemy implements a `get_or_404` helper which does something similar.
# * `send_file` tells Flask to send a file response instead of something more typical.
# 
# This is all you need for your API to interact and stream. Except data. That's what `manager.py` is for.

# In[ ]:

#manager.py
from app import app, db, ma, models, serializers, utils
from flask.ext.script import Manager

manager = Manager(app)

@manager.option('-d', '--dir', dest='dir')
def add(dir):
    utils.store_directory(dir)

@manager.shell
def _shell_context():
    return dict(app=app, db=db, ma=ma, models=models, serials=serializers, utils=utils)

if __name__ == "__main__":
    manager.run()


# Flask-Script is an incredibly useful extension that allows you to interact with your application on the command line. Consider this an extremely brief explaination.
# 
# * Manager.option allows you to pass CLI arguments into your functions easily.
# * Manager.shell is a predetermined command that sets up a shell context for your application. All it requires is to know what to pass in.
# 
# The utils file is the only one I haven't covered yet. These are functions and things that will assist in the running of the application but are otherwise unconnected to anything else.

# In[ ]:

#app/utils.py
import os
from uuid import uuid4
from mutagenx import File
from .models import db, Album, Artist, Track

valid_types=('m4a', 'flac', 'mp3', 'ogg', 'oga')


def find(basedir, valid_types=valid_types):
    '''Utilize os.walk to only select out the files we'd like to potentially
    parse and yield them one at a time.'''
    basedir = os.path.abspath(basedir)
    for current, dirs, files in os.walk(basedir):
        if not files:
            continue
        for file in files:
            if file.endswith(valid_types):
                yield os.path.join(os.path.abspath(current), file)

def adaptor(track):
    return dict(
        artist=track['artist'][0],
        album=track['album'][0],
        position=int(track['tracknumber'][0].split('/')[0]),
        length=int(track.info.length),
        location=track.filename,
        name=track['title'][0],
        stream=str(uuid4())
        )

def adapt_track(track, adaptor=adaptor):

    info = adaptor(track)

    artist = Artist.query.filter(Artist.name == info['artist']).first()
    if not artist:
        artist = Artist(name=info['artist'])
        db.session.add(artist)
    info['artist'] = artist

    album = Album.query.filter(Album.name==info['album']).first()
    if not album:
        album = Album(name=info['album'], artist=artist)
        db.session.add(album)
    info['album'] = album

    track = Track.query.filter(Track.name==info['name'])
    track = track.filter(Track.album_id==album.id)
    track = track.first()
    if not track:
        track = Track(**info)
        db.session.add(track)

    return artist, album, track


def store_directory(basedir, valid_types=valid_types, adaptor=adaptor):
    for file in find(basedir, valid_types):
        file = File(file, easy=True)
        
        try:
            artist, album, track = adapt_track(file)
            print(
                " * Storing: {0.name} - {1.name} - {2.position:2>0} - {2.name}"
                "".format(artist, album, track))
            db.session.commit()
        except KeyError:
            pass


# Now, to add information to the database, you'll simply do:
# 
#     python manager.py add -d /home/justanr/Music/Acid Bath
#     
# And you'll get back something like this:
# 
#      * Storing: Acid Bath - When the Kite String Pops - 5 - Jezebel
#      * Storing: Acid Bath - When the Kite String Pops - 11 - The Morticians Flame
#      * Storing: Acid Bath - When the Kite String Pops - 14 - Cassie Eats Cockroaches
#      * Storing: Acid Bath - When the Kite String Pops - 4 - Finger Paintings of the Insane
#      * Storing: Acid Bath - When the Kite String Pops - 9 - Toubabo Koomi
#      * Storing: Acid Bath - When the Kite String Pops - 13 - The Bones of Baby Dolls
#      * Storing: Acid Bath - When the Kite String Pops - 6 - Scream of the Butterfly
#      * Storing: Acid Bath - When the Kite String Pops - 10 - God Machine
#      * Storing: Acid Bath - When the Kite String Pops - 2 - Tranquilized
#      * Storing: Acid Bath - When the Kite String Pops - 8 - Dope Fiend
#      * Storing: Acid Bath - When the Kite String Pops - 3 - Cheap Vodka
#      * Storing: Acid Bath - When the Kite String Pops - 7 - Dr. Seuss Is Dead
#      * Storing: Acid Bath - When the Kite String Pops - 12 - What Color Is Death
#      * Storing: Acid Bath - When the Kite String Pops - 1 - The Blue
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 6 - Old Skin
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 10 - New Corpse
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 5 - Locust Spawning
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 12 - Ode of the Peagan
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 7 - New Death Sensation
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 11 - Dead Girl
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 4 - Diäb Soulé
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 3 - Graveflower
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 9 - 13 Fingers
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 2 - Bleed Me an Ocean
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 8 - Venus Blue
#      * Storing: Acid Bath - Paegan Terrorism Tactics - 1 - Paegan Love Song
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 7 - Finger Paintings of the Insane
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 6 - Dope Fiend
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 8 - Jezebel
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 10 - Venus Blue
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 11 - Bleed Me an Ocean
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 3 - Scream of the Butterfly
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 9 - The Bones of Baby Dolls
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 2 - What Color Is Death
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 1 - Dr. Seuss Is Dead
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 5 - The Mortician's Flame
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 12 - Graveflower
#      * Storing: Acid Bath - Demos: 1993 - 1996 - 4 - God Machine
# 
# Running the server is as simple as `python manager.py runserver -p 5000 -h 0.0.0.0`. From there navigating to `127.0.0.1:5000/artist/` will output something like this:
# 
#     {
#         "artists": [
#             {
#                 "albums": [
#                     {
#                         "id": 3,
#                         "links": {
#                             "collection": "/album/",
#                             "self": "/album/3/"
#                         },
#                         "name": "Demos: 1993 - 1996",
#                         "tracks": [
#                             {
#                                 "id": 35,
#                                 "length": "05:39",
#                                 "links": {
#                                     "collection": "/track/",
#                                     "self": "/track/35/"
#                                 },
#                                 "name": "Dr. Seuss Is Dead",
#                                 "position": 1,
#                                 "stream": "5ef608d4-aca1-496d-a876-0778c2e6ea6b"
#                             }
#                         ]
#                     }
#                 ],
#                 "id": 1,
#                 "links": {
#                     "collection": "/artist/",
#                     "self": "/artist/1/"
#                 },
#                 "name": "Acid Bath"
#             }
#         ]
#     }
# 
# From there, navigating to `127.0.0.1:5000/stream/5ef608d4-aca1-496d-a876-0778c2e6ea6b/` will play the song.

# From Here
# ---------
# There's many things wrong with the application. Flask is server static content, which is a job better served by a proper web server, such as Nginx. And we're just glossing over the issue of the application blowing up when it hits an object with only partial data. We're also storing objects one at a time instead of committing a batch of objects (say ten or fifteen at a time, or even a whole album or artist discography).
# 
# But this also lays the foundations of a much broader application. There's several features I intend on adding and building on to here until there's a full featured API.
# 
# But for now, feel free to tinker and change. If you develop something, submit me [a pull request](https://github.com/justanr/FlaskAmp/).
