import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jesus-is-our-only-savior'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'db.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_DEBUG=1
    TEMPLATES_AUTO_RELOAD=1
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['ilovecheesecake85@gmail.com']
    AVATAR_PATH = os.path.join(basedir, 'app/static/avatars')
    UPLOAD_PATH = os.path.join(basedir, 'app/uploads/images')
    AUPLOAD_PATH = os.path.join(basedir, 'app/uploads/audio')
    UPLOAD_FOLDER = 'app/uploads/audio'
    LANGUAGES = ['en', 'ko', 'ru']
    
    
    POSTS_PER_PAGE = 25
    SONGS_PER_PAGE = 50
    ITEMS_PER_PAGE = 100