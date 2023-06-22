from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import app, db, login
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt


# many to many relationship followed and followers --> user folloring another user
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

list_user = db.Table('list_user',
                     db.Column('lists_id', db.Integer, db.ForeignKey('lists.id')), 
                     db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

songcart = db.Table('Songcart',
                    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                    db.Column('listitem_id', db.Integer, db.ForeignKey('listitem.id')),
                    )

rolestable = db.Table('RolesTable',
                    db.Column('listitem_id', db.Integer, db.ForeignKey('listitem.id')),
                    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                    )

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Integer, db.ForeignKey('listitem.id'))
    # role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    lists = db.relationship('Lists', backref='creator', lazy='dynamic') 
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    songs = db.relationship('Song', backref='publisher', lazy='dynamic')
    # lists = db.relationship('Worshiplist', backref='leader', lazy='dynamic')
    cart = db.relationship('ListItem', secondary=songcart, backref=db.backref('owner', lazy='dynamic'))
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    #to use werkzeug hashing for password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
    
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
           
@login.user_loader
def load_user(id):
    return User.query.get(int(id)) #flask-login passes id as string, thus converted to int.
    
class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))
    
    def __repr__(self):
        return '<Post {}>'.format(self.body)

songtags = db.Table('songtags', 
                    db.Column('song_id', db.Integer, db.ForeignKey('song.id')), 
                    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

translation = db.Table('translation',
    db.Column('song_id', db.Integer, db.ForeignKey('song.id')),
    db.Column('translated_id', db.Integer, db.ForeignKey('song.id')))

medialinks = db.Table('medialinks', 
                    db.Column('song_id', db.Integer, db.ForeignKey('song.id')), 
                    db.Column('mlink_id', db.Integer, db.ForeignKey('mlinks.id')))

songlistitem = db.Table('songlistitem',
                    db.Column('listitem_id', db.Integer, db.ForeignKey('listitem.id')),
                    db.Column('song_id', db.Integer, db.ForeignKey('song.id')))


    
class Song(db.Model):
    __tablename__ = 'song'
    __searchable__ = ['title', 'singer', 'lyrics']
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=True)
    singer = db.Column(db.String(140), index=True)
    info = db.Column(db.String(140))
    key = db.Column(db.Integer)
    lyrics = db.Column(db.Text)
    language = db.Column(db.Integer)
    # later need to find a way to bind same songs in other languages (maybe same code as with following)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tags = db.relationship('Tag', secondary=songtags, 
                           backref=db.backref('songs', lazy='dynamic'), lazy='dynamic')
    translated = db.relationship(
        'Song', secondary=translation,
        primaryjoin=(translation.c.song_id == id),
        secondaryjoin=(translation.c.translated_id == id),
        backref=db.backref('translation', lazy='dynamic'), lazy='dynamic')
    media = db.relationship('Mlinks', secondary=medialinks, 
                           backref=db.backref('songs', lazy='dynamic'), lazy='dynamic')
    
    def __repr__(self):
        return '<Song {}>'.format(self.title)
    
    def add_transl(self, song):
        if not self.transl_exist(song):
            self.translated.append(song)

    def remove_transl(self, song):
        if self.transl_exist(song):
            self.translated.remove(song)

    def transl_exist(self, song):
        return self.translated.filter(
            translation.c.translated_id == song.id).count() > 0
    
   
class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70))
    
class Mlinks(db.Model): # this table will have M-M relationship with Song Table
    __tablename__ = 'mlinks'
    id  = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), index=True)
    mtype = db.Column(db.Integer)
    murl = db.Column(db.String(140))
    

eventitems = db.Table('Eventitems',
                    db.Column('lists_id', db.Integer, db.ForeignKey('lists.id')),
                    db.Column('listitem_id', db.Integer, db.ForeignKey('listitem.id')),
                    )

class Lists(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    date_time = db.Column(db.DateTime, index=True)
    date_end = db.Column(db.DateTime)
    # ability to add youtube clips for lists of songs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mlink = db.Column(db.String(140))
    status = db.Column(db.Integer, default=0) # 0 - in progress, 1 = Ready, 2 - past 
    list_title = db.Column(db.String(100), default='Sunday service')
    # many-to-many relationship with user. so we can assign specific people to this list
    assigned = db.relationship('User', secondary=list_user, backref=db.backref('minister', lazy='dynamic'), lazy='dynamic')
    items = db.relationship('ListItem', secondary=eventitems, backref=db.backref('list', lazy='dynamic'), lazy='dynamic')
    
    def __repr__(self):
        return '<date {}>'.format(self.date_time)
    
class ListItem(db.Model):
    __tablename__ = 'listitem'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    desired_key = db.Column(db.Integer)
    listorder = db.Column(db.Integer)
    notes = db.Column(db.Text)
    role = db.relationship('User', secondary=rolestable, backref=db.backref('roles', lazy='dynamic'), lazy='dynamic')
    song = db.relationship('Song', secondary=songlistitem, backref=db.backref('inlist', lazy='dynamic'), lazy='dynamic')
    def __repr__(self):
        return '<ListItems {}>'.format(self.title)        