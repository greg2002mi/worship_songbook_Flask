from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import app, db, login
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt


          
# class Permission:
#     FOLLOW = 1
#     COMMENT = 2
#     WRITE = 4
#     MODERATE = 8
#     ADMIN = 16

# setting permissions for site
# class Role(db.Model):
#     __tablename__ = 'roles'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), unique=True)
#     default = db.Column(db.Boolean, default=False, index=True)
#     permissions = db.Column(db.Integer)
#     users = db.relationship('User', backref='role')
    
#     def __init__(self, **kwargs):
#         super(Role, self).__init__(**kwargs)
#         if self.permissions is None:
#             self.permissions = 0
    
#     def add_permission(self, perm):
#         if not self.has_permission(perm):
#             self.permissions += perm
    
#     def remove_permission(self, perm):
#         if self.has_permission(perm):
#             self.permissions -= perm
    
#     def reset_permissions(self):
#         self.permissions = 0
    
#     def has_permission(self, perm):
#         return self.permissions & perm == perm
    
#     def __repr__(self):
#         return '<Role {}>'.format(self.name)

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.Integer, db.ForeignKey('listitem.id'))
    # role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    mlinks = db.relationship('Lists', backref='creator', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    songs = db.relationship('Song', backref='publisher', lazy='dynamic')
    # lists = db.relationship('Worshiplist', backref='leader', lazy='dynamic')
    cart = db.relationship('ListItem', secondary=songcart, backref=db.backref('owner', lazy='dynamic'), lazy='dynamic')
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
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
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
  # many to many relationship sermon and songs  
# songlist = db.Table('songlist', 
#                     db.Column('sermon_id', db.Integer, db.ForeignKey('sermon.id')), 
#                     db.Column('song_id', db.Integer, db.ForeignKey('song.id')))

    
class Song(db.Model):
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
    listitem_id = db.Column(db.Integer, db.ForeignKey('listitem.id'))
    tags = db.relationship('Tag', secondary=songtags, 
                           backref=db.backref('songs', lazy='dynamic'), lazy='dynamic')
    translated = db.relationship(
        'Song', secondary=translation,
        primaryjoin=(translation.c.song_id == id),
        secondaryjoin=(translation.c.translated_id == id),
        backref=db.backref('translation', lazy='dynamic'), lazy='dynamic')
    media = db.relationship('Mlinks', secondary=medialinks, 
                           backref=db.backref('songs', lazy='dynamic'), lazy='dynamic')
    # inlist = db.relationship(
    #     'Sermon', secondary=songlist, backref='song')
    
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
    
    # assigning song to tags
    # def add_tag(self, tag):
    #     if not self.in_tags(tag):
    #         self.tags.append(tag)

    # def remove_tag(self, tag):
    #     if self.in_tags(tag):
    #         self.tags.remove(tag)
    
    # def in_tags(self, tag):
    #     return self.tags.filter(songtags.c.tag_id == tag.id).count() > 0
    
        
    # many to many relationship genre and songs
   
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    
class Mlinks(db.Model): # this table will have M-M relationship with Song Table
    id  = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), index=True)
    mtype = db.Column(db.Integer)
    murl = db.Column(db.String)
    
    # mtype will distinguish youtube, mp3, or pictures
    
    # def __repr__(self):
    #     return '<Tag {}>'.format(self.name)

 # need to make a list of songs, something like favorites. debating on relationship and structure
# class Worshiplist(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     sermon_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     worship_lists = db.relationship('Song', backref='songs', lazy='dynamic')

class Lists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    date_time = db.Column(db.DateTime, index=True)
    date_end = db.Column(db.DateTime)
    # ability to add youtube clips for lists of songs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mlink = db.Column(db.String)
    status = db.Column(db.Integer, default=0) # 0 - in progress, 1 = Ready, 2 - past 
    list_title = db.Column(db.String, default='Sunday service')
    # many-to-many relationship with user. so we can assign specific people to this list
    assigned = db.relationship('User', secondary=list_user, backref=db.backref('minister', lazy='dynamic'), lazy='dynamic')
    items = db.relationship('ListItem', backref='list', lazy='dynamic')
    
    def __repr__(self):
        return '<date {}>'.format(self.date_time)
    
class ListItem(db.Model):
    __tablename__ = 'listitem'
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'))
    title = db.Column(db.String(140))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    song = db.relationship('Song', backref='inlist', lazy='dynamic')
    desired_key = db.Column(db.Integer)
    listorder = db.Column(db.Integer)
    notes = db.Column(db.Text)
    role = db.relationship('User', backref='assigned', lazy='dynamic')
    
    def __repr__(self):
        return '<ListItems {}>'.format(self.title)        