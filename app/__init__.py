from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class, AUDIO
from config import Config
from flask_login import LoginManager
from flask_mail import Mail
import logging, os, imghdr, magic
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel





app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'unfailing_soul'
app.config['MAIL_PASSWORD'] = 'Shunya1104@'
app.config['IMAGE_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.svg', '.bmp', '.webp']
app.config['AUDIO_EXTENSIONS'] = ['.wav', '.mp3', '.aac', '.ogg', '.oga', '.flac']
# app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
# app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_PATH']
app.config['AUPLOAD_PATH']
app.config['AVATAR_PATH']
app.config['UPLOAD_FOLDER']
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)

# images = UploadSet('images', IMAGES)
# audio = UploadSet('audio', AUDIO)
# configure_uploads(app, images)
# configure_uploads(app, audio)
# patch_request_class(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

def validate_image(stream, ori_ext):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if (format != 'jpeg' or ori_ext == 'jpeg') else 'jpg')

def validate_audio(stream, ori_ext):
    file_signature = magic.from_buffer(stream.read(2048), mime=True)
    stream.seek(0)
    print('File Signature:', file_signature)
    print('Original Extension:', ori_ext)
    if file_signature.startswith('audio/'):
        return ori_ext.lower()
    return None
    
from app import routes, models, error, core, email

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Church-Library',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/library.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Church startup')    