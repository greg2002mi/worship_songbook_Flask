from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddSong, EditSong, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, Transpose
from app.forms import AddTag, TagsForm
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Song, Post, Tag
from datetime import datetime
from app.email import send_password_reset_email
from app.core import Chordpro_html
import logging

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home Page', form=form, posts=posts.items, 
                           next_url=next_url, prev_url=prev_url)

@app.route('/songbook')
def songbook():
    page = request.args.get('page', 1, type=int)
    songs = Song.query.order_by(Song.title.desc()).paginate(
        page=page, per_page=app.config['SONGS_PER_PAGE'], error_out=False)
    next_url = url_for('songbook', page=songs.next_num) \
        if songs.has_next else None
    prev_url = url_for('songbook', page=songs.prev_num) \
        if songs.has_prev else None
    return render_template('songbook.html', title='Songbook', songs=songs.items, 
                           next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    # if user == 'admin':
        # post = Post.query.all()
        # if admin show all the posts
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)    

@app.route('/add_song', methods=['GET', 'POST'])
@login_required
def add_song():
    form = AddSong()
    if form.validate_on_submit():
        song = Song(title=form.title.data, info=form.info.data, singer=form.singer.data, key=form.key.data, language=form.language.data, lyrics=form.lyrics.data, publisher=current_user)
        db.session.add(song)
        db.session.commit()
        flash('a new song has been added and saved')
        return redirect(url_for('songbook'))
    return render_template('add_song.html', title='Add a song', form=form)

# @app.route('/add_sermon', methods=['GET', 'POST'])
# @login_required
# def add_sermon():
#     form = AddSermon()
#     if form.validate_on_submit():
#         sermon = Sermon(date_time=form.date_time.data, sermon_title=form.sermon_title.data, leader_name=form.leader_name.data, publisher=current_user)
#         db.session.add(sermon)
#         db.session.commit()
#         flash('Sermon is set')
#         return redirect(url_for('sermons'))
#     return render_template('add_sermon.html', title='Set new sermon', form=form)

# @app.route('/edit_sermon/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_sermon(id):
#     sermon = Sermon.query.get_or_404(id)
#     # if current_user != song.publisher and not current_user.can(Permission.ADMIN):
#     # if current_user != song.publisher:
#     #     abort(403)
#     form = EditSermon()
#     if form.validate_on_submit():
#         sermon.date_time = form.date_time.data
#         sermon.sermon_title = form.sermon_title.data
#         sermon.leader_name = form.leader_name.data
#         db.session.add(sermon)
#         db.session.commit()
#         flash('Changes to the sermon have been saved.')
#         return redirect(url_for('sermons')) #later change it to view song mode
#     elif request.method == 'GET':
#         form.date_time.data = sermon.date_time
#         form.sermon_title.data = sermon.sermon_title
#         form.leader_name.data = sermon.leader_name
#     return render_template('edit_sermon.html', title='Edit Sermon', form=form) 

# @app.route('/sermons')
# def sermons():
#     page = request.args.get('page', 1, type=int)
#     sermons = Sermon.query.order_by(Sermon.date_time.desc()).paginate(
#         page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
#     next_url = url_for('sermons', page=sermons.next_num) \
#         if sermons.has_next else None
#     prev_url = url_for('sermons', page=sermons.prev_num) \
#         if sermons.has_prev else None
#     return render_template('sermons.html', title='Sermons', sermons=sermons.items, 
#                            next_url=next_url, prev_url=prev_url)

@app.route('/tag_list', methods=['GET', 'POST'])
def tag_list():
    form = AddTag()
    tags = Tag.query.all()
    if form.validate_on_submit():
        t = Tag(name=form.name.data) 
        db.session.add(t)
        db.session.commit()
        flash('A new tag has been saved.')
        return redirect(url_for('tag_list'))      
    return render_template('tag_list.html', title='Tag list', tags=tags, form=form)

@app.route('/edit_song/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_song(id):
    song = Song.query.get_or_404(id)
    key = request.args.get('key', type=int)
    ori_key_int = song.key
    if key is None:
        key = ori_key_int
    # if current_user != song.publisher and not current_user.can(Permission.ADMIN):
    if current_user != song.publisher:
        abort(403)
    form = EditSong()
    if form.validate_on_submit():
        song.title = form.title.data
        song.singer = form.singer.data
        song.info = form.info.data
        song.key = form.key.data
        song.language = form.language.data
        song.lyrics = form.lyrics.data
        db.session.add(song)
        db.session.commit()
        flash('Changes to the song have been saved.')
        return redirect(url_for('.view_song', id=song.id, key=key)) #later change it to view song mode
    elif request.method == 'GET':
        form.title.data = song.title
        form.singer.data = song.singer
        form.info.data = song.info
        form.key.data = song.key
        form.language.data = song.language
        form.lyrics.data = song.lyrics
    return render_template('edit_song.html', title='Edit Song', form=form) 

@app.route('/view_song', methods=['GET', 'POST'])
def view_song():
    id = request.args.get('id', type=int)
    key = request.args.get('key', type=int)
    song = Song.query.get_or_404(id)
    tags = Tag.query.all()
    tag_states = {}
    tagged_list = ([tagged.name for tagged in song.tags])
    # if I want to find tags based on songs tagged
    # selected_tags = Tag.query.filter(Tag.songs.any(song.id==id)).all()
    # tagged_list_int = ([t.id for t in tags])
    # print(tagged_list_int)
    # tags = Tag.query.filter(Tag.id.in_(tagged_list_int)).all()
    # print(tags)
    ori_key_int = song.key
    lyrics = song.lyrics
    form = Transpose()
    tags_form = TagsForm()
    # populate choices for tags_form from db
    choices = [(t.id, t.name) for t in tags]
    tags_form.name.choices = choices
    print(choices)
    keyset = ('Empty', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
    if key is None:
        transpose = ori_key_int
    else: 
        transpose = int(key)
    # to send original key as string
    ori_key = keyset[ori_key_int]
    if transpose != ori_key_int:
        ori_key = ori_key + " | transposed to " + keyset[transpose]
    showchords = True
    html = Chordpro_html(lyrics, showchords, ori_key_int, transpose)
    only_lyrics = Chordpro_html(lyrics, False, 0, 0)
    if song is None:
        flash('Current song does not have lyrics')
        return redirect(url_for('songbook'))
    else:
        if form.validate_on_submit():
            # Handle the submit of transpose chord action
            key = form.key.data
            return redirect(url_for('.view_song', id=song.id, key=key))
        elif request.method == "POST" and tags_form.validate_on_submit():
            # Handle addition of tags to a song
            logging.basicConfig(filename='debug.log', level=logging.DEBUG)
            selected_tags = request.form['name']
            logging.debug(selected_tags)
            for tag_id in selected_tags:
                t = Tag.query.get(tag_id)
                print(t)
                if t is not None and t not in song.tags:
                    song.tags.append(t)
            # list = Tag.query.filter(Tag.id.in_(selected_tags)).all()
            # for t in list:
            #     is_tagged = t in song.tags.all()
            #     if not is_tagged:
            #         song.tags.append(t)
            #         db.session.add(song)
            #         db.session.commit()
            # for t in tags:
            #     song.add_tag(t)
            db.session.add(song)
            db.session.commit()
            # return redirect(url_for('.view_song', id=song.id, key=key))
        elif request.method == 'GET':
            form.key.data = song.key
            for tag in tags:
                tag_states[tag.id] = tag in song.tags
            print(tag_states)
        return render_template('view_song.html', title='View Song', html=html, tagged_list=tagged_list, tag_states=tag_states, tags=tags, tags_form=tags_form, only_lyrics=only_lyrics, song=song, form=form, ori_key=ori_key)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

# @app.route('/adding_genre', methods=['POST'])
# @login_required
# def adding_genre(username):
#     id = request.args.get('id', type=int)
    
#     form = SelectGenre()
#     if form.validate_on_submit():
#         song = Song.query.get_or_404(id)
        
#         if song is None:
#             flash('Song {} not found.'.format(str(id)))
#             return redirect(url_for('view_song'))
#         song.adding_genre(genre)
#         db.session.commit()
#         flash('You are following {}!'.format(username))
#         return redirect(url_for('user', username=username))
#     else:
#         return redirect(url_for('index'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)