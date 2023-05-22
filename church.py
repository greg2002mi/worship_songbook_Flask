from app import app, db
from app.models import User, Post, Song, Tags

#to load database and all the tables into shell on each shell run
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Song': Song, 'Tags': Tags}