from flask import render_template, flash, redirect, url_for, request, abort, send_from_directory, jsonify
from app import app, db, validate_image
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddSong, EditSong, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, Transpose
from app.forms import AddTag, TagsForm, SongsForm, AddMedia, AddEvent, Assign2Event
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Song, Post, Tag, Mlinks, Lists, ListItem
from datetime import datetime
from app.email import send_password_reset_email
from app.core import Chordpro_html
from werkzeug.utils import secure_filename
from functools import wraps
import os
#import logging

keyset = ('Empty', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
lang = ('None', 'Eng', 'Kor', 'Rus')

def limit_content_length(max_length):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None and cl > max_length:
                abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

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
    form = EmptyForm()
    keyset = ('Empty', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
    page = request.args.get('page', 1, type=int)
    songs = Song.query.order_by(Song.title.desc()).paginate(
        page=page, per_page=app.config['SONGS_PER_PAGE'], error_out=False)
    next_url = url_for('songbook', page=songs.next_num) \
        if songs.has_next else None
    prev_url = url_for('songbook', page=songs.prev_num) \
        if songs.has_prev else None
    return render_template('songbook.html', title='Songbook', songs=songs.items, 
                           next_url=next_url, prev_url=prev_url, keyset=keyset, lang=lang, form=form)

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

@app.route('/upload_avatar', methods=['GET', 'POST'])
@limit_content_length(1024 * 1024)
def upload_avatar():
    files = os.listdir(app.config['AVATAR_PATH'])
    username = current_user.username
    if request.method == 'POST':
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['IMAGE_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream, file_ext):
                return "Invalid image", 400
            uploaded_file.save(os.path.join(app.config['AVATAR_PATH'], filename))
        return redirect(url_for('edit_profile'))
    return render_template('upload_avatar.html', username=username, files = files)

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['AVATAR_PATH'], filename)

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
    untag_form = EmptyForm()
    tags = Tag.query.all()
    if form.validate_on_submit():
        t = Tag(name=form.name.data) 
        db.session.add(t)
        db.session.commit()
        flash('A new tag has been saved.')
        return redirect(url_for('tag_list'))      
    return render_template('tag_list.html', title='Tag list', tags=tags, form=form, untag_form=untag_form)

# @app.route('/img_upload', methods=['GET', 'POST'])
# @login_required
# def img_upload():
#     songid = request.args.get('songid', type=int)
#     song = Song.query.filter_by(id=songid).first_or_404()
#     mtype = request.args.get('mtype', type=int)
#     # imgform = ImageUpload()
#     # how many links does song media have
#     if song.media is None:
#         num = 1
#     else:
#         media = song.media.all()
#         num = len(media) + 1
#     if mtype is None:
#         flash('type variable is None.')
#         return redirect(url_for('.img_upload', songid=song.id)) 
#     if request.method == 'POST':
#         uploaded_file = request.files['file']
#         for uploaded_file in request.files.getlist('file'):
#             filename = secure_filename(uploaded_file.filename)
#             if filename != '' and mtype == 3:
#                 file_ext = os.path.splitext(filename)[1]
#                 if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(uploaded_file.stream):
#                     abort(400)
#                 # filename = images.save(imgform.image.data, name="{}_image_{}.jpg".format(song.id, str(num)))
#                 uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
#                # file_url = images.url(filename)
#             return redirect(url_for('.img_upload', songid=song.id))
#         # elif request.method == 'GET':
#     #    return render_template('img_upload.html', title='Media upload', imgform=imgform)

#     return render_template('img_upload.html', title='Media upload')
       # filename = images.save(imgform.image.data, name=f"{}.jpg".format(song.title))
# @app.route('/add_media', methods=['GET', 'POST'])
# def add_media():
#     sid = request.args.get('sid', type=int)
#     song = Song.query.get(sid)
#     form = AddMedia()
#     if form.submit():
#         option = form.mtype.data
#         if option == 1:
#             #youtube link
#             media = Mlinks(murl = form.murl.data, mtype = form.mtype.data)
#             db.session.add(media)
#         elif option in (2, 3):
#             files = flask.request.files.getlist("file")
#             for file in files:
#     #             file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
#     #             media = Mlinks(murl = "PATH TO FILE", mtype = form.mtype.data)
#     # # need to save files to folder and save its path to murl

#     # after session.commit() link to Song.media.append(media)            
                
                
    
#         db.session.commit()
            
    # if request.method == "POST":
    #     return jsonify(request.form)
        # mlinks_count = int(request.form.get('mlinks_count'))
        # for mlink_index in range(1, mlinks_count + 1):
        #     mtype_field = f'mtype_{mlink_index}'
        #     murl_field = f'murl_{mlink_index}'
        #     mtype = int(request.form.get(mtype_field))
        #     murl = request.form.get(murl_field)
        #     media = Mlinks(mtype=mtype, murl=murl)            
        #     song.media.append(media)
        #     db.session.add(song)
        #     db.session.commit()
        # flash('New link(s) added to library.')
    #     return redirect(url_for('.view_song', sid=song.id, key=song.key))
    # else:     
    #     return render_template('add_media.html', title='Media Library', form=form)

@app.route('/tag_songlist')
def tag_songlist():
    tagid = request.args.get('tagid', type=int)
    tag = Tag.query.filter_by(id=tagid).first_or_404()
    page = request.args.get('page', 1, type=int)
    songs = tag.songs.order_by(Song.title).paginate(
        page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    next_url = url_for('tag_songlist', tagid=tag.id, page=songs.next_num) \
        if songs.has_next else None
    prev_url = url_for('tag_songlist', tagid=tag.id, page=songs.prev_num) \
        if songs.has_prev else None
    form = EmptyForm()
    return render_template('tag_songlist.html', tag=tag, songs=songs.items,
                            next_url=next_url, prev_url=prev_url, form=form)

@app.route('/untag', methods=['POST'])
@login_required
def untag():
    tagid = request.args.get('tagid', type=int)
    songid = request.args.get('songid', type=int)
    form = EmptyForm()
    if form.validate_on_submit():
        tag = Tag.query.filter_by(id=tagid).first_or_404()
        song = Song.query.filter_by(id=songid).first_or_404()
        if tag is None:
            flash('Tag {} not found.'.format(tag.name))
            return redirect(url_for('tag_list'))
        if song is None:
            flash('Song {} not found.'.format(song.title))
            return redirect(url_for('tag_songlist', tagid=tagid))
        song.tags.remove(tag)#issue. does not remove tag from song.
        db.session.commit()
        flash('Song has been removed from tag {}.'.format(tag.name))
        return redirect(url_for('tag_songlist', tagid=tagid))
    return redirect(url_for('tag_list'))

@app.route('/untagall', methods=['POST'])
@login_required
def untagall():
    id = request.args.get('id', type=int)
    untagall_form = EmptyForm()
    if untagall_form.submit():
        song = Song.query.filter_by(id=id).first_or_404()
        if song is None:
            flash('Song {} not found.'.format(song.title))
            return redirect(url_for('.view_song', id=id))
        song.tags=[]
        db.session.commit()
        flash('All tags for {} have been untagged.'.format(song.title))
    return redirect(url_for('.view_song', id=id))

@app.route('/remove_tag', methods=['POST'])
@login_required
def remove_tag():
    # first untag all songs from specific tag in relational database
    # second remove tag from Tag database
    tagid = request.args.get('tagid', type=int)
    tag = Tag.query.filter_by(id=tagid).first_or_404() 
    untag_form = EmptyForm()
    if untag_form.validate_on_submit():
        if tag is None:
            flash('Tag {} does not exist.'.format(tag.name))
            return redirect(url_for('tag_list'))
        if tag.songs is not None:
            t_songs = tag.songs.all()
            for ts in t_songs:
                ts.tags.remove(tag)   
        db.session.delete(tag)
        db.session.commit()
        flash('Tag has been unlinked from all songs and removed from Database')
        return redirect(url_for('tag_list'))
    else:
        return redirect(url_for('tag_list'))


# !!!! - remove all song to song links before deleting song    
@app.route('/delete_song', methods=['POST'])
@login_required
def delete_song():
    songid = request.args.get('songid', type=int)
    delete_form = EmptyForm()
    if delete_form.validate_on_submit():
        song = Song.query.filter_by(id=songid).first_or_404() 
        if song is None:
            flash('Song {} not found.'.format(song.title))
            return redirect(url_for('songbook'))
        if song.tags is not None:
            songtags = song.tags.all()
            for s_tags in songtags:
                s_tags.songs.remove(song)
        if song.translated is not None:
            transl = song.translated.all()
            for ts in transl:
                ts.translated.remove(song)
        db.session.delete(song)
        db.session.commit()
        flash('Song {} is deleted.'.format(song.title))
        return redirect(url_for('songbook'))
    else:
        return redirect(url_for('songbook'))     

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

@app.route('/add_transl/<int:id>', methods=['POST'])
@login_required
def add_transl(id):
    # cur_song_id = request.args.get('cur_song_id', type=int)
    transl_form = SongsForm()
    if request.method == "POST" and transl_form.submit():
        cur_song = Song.query.filter_by(id=id).first_or_404() 
        tr_song_id = transl_form.tr_song_id.data
        tr_song = Song.query.filter_by(id=int(tr_song_id)).first_or_404() 
        if cur_song is None or tr_song is None:
            flash('Song {} or {} not found.'.format(cur_song.title, tr_song.title))
            return redirect(url_for('songbook'))
        if cur_song.language == tr_song.language:
            flash('You cannot link songs of same language!')
            return redirect(url_for('.view_song', id=cur_song.id))
        # cur_song.add_transl(tr_song)
        cur_song.translated.append(tr_song)
        db.session.add(cur_song)
        db.session.commit()
        flash('The song {} now has a translated song {}.'.format(cur_song.title, tr_song.title))
        return redirect(url_for('.view_song', id=id))
    else:
        flash('Issues: Validation not passed.')
        return redirect(url_for('.view_song', id=id))
    
@app.route('/remove_transl', methods=['POST'])
@login_required
def remove_transl():
    cursong_id = request.args.get('cursong_id', type=int)
    selsong_id = request.args.get('selsong_id', type=int)
    remove_transl_form = EmptyForm()
    if remove_transl_form.validate_on_submit():
        cursong = Song.query.filter_by(id=cursong_id).first_or_404() 
        selsong = Song.query.filter_by(id=selsong_id).first_or_404() 
        if cursong is None or selsong is None:
            flash('Song {} or {} not found.'.format(cursong.title, selsong.title))
            return redirect(url_for('.view_song', id=cursong.id))
        if selsong not in cursong.translated:
            flash('Current song does not have a link with selected song!')
            return redirect(url_for('.view_song', id=cursong.id))
        # cur_song.add_transl(tr_song)
        cursong.translated.remove(selsong)
        db.session.add(cursong)
        db.session.commit()
        flash('The song {} and  song {} are now not linked.'.format(cursong.title, selsong.title))
        return redirect(url_for('.view_song', id=cursong.id))
    else:
        flash('Issues: Validation not passed.')
        return redirect(url_for('.view_song', id=cursong_id))

@app.route('/view_song', methods=['GET', 'POST'])
def view_song():
    id = request.args.get('id', type=int)
    key = request.args.get('key', type=int)
    song = Song.query.get_or_404(id)
    tags = Tag.query.all()
    media = song.media.all()
    tag_states = {}
    tagged_list = ([tagged.name for tagged in song.tags])
    ori_key_int = song.key
    lyrics = song.lyrics
    form = Transpose()
    transl_form = SongsForm()
    remove_transl_form = EmptyForm()
    untagall_form = EmptyForm()
    #to get a list of songs with condition, other language, and not already linked ones
    other_songs = Song.query.filter(Song.language!=song.language).all()
    if song.translated is not None:
        linked = song.translated.all()
        for l in linked:
            other_songs.remove(l)
    tr_list = [(s.id, s.title) for s in other_songs]
    transl_form.tr_song_id.choices = tr_list
    # list of translated songs
    t1_songlist = song.translated.order_by(Song.title).all()
    t2_songlist = song.translation.order_by(Song.title).all()
    t_songlist = list(t1_songlist)
    for song_obj in t2_songlist:
        if song_obj not in t_songlist:
            t_songlist.append(song_obj)
    delete_form = EmptyForm()
    tags_form = TagsForm(obj=song)
    # populate choices for tags_form from db
    choices = [(t.id, t.name) for t in tags]
    tags_form.name.choices = choices
    # print(choices)
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
        elif request.method == 'GET':
            form.key.data = song.key
            for tag in tags:
                tag_states[tag.id] = tag in song.tags
        return render_template('view_song.html', title='View Song', html=html, transl_form=transl_form, 
                               remove_transl_form=remove_transl_form, delete_form=delete_form, tagged_list=tagged_list, 
                               tag_states=tag_states, tags_form=tags_form, only_lyrics=only_lyrics, song=song, form=form, 
                               ori_key=ori_key, t_songlist=t_songlist, lang=lang, untagall_form=untagall_form, media=media)

@app.route('/upload_images', methods=['POST'])
@limit_content_length(10 * 1024 * 1024)
def upload_images():
    id = request.args.get('id', type=int)
    song = Song.query.get_or_404(id)
    mtype = request.args.get('mtype', type=int)
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if song.media is None:
        num = 1
    else:
        media = song.media.all()
        num = len(media) + 1
    if mtype is None:
        flash('type variable is None.')
        return redirect(url_for('.img_upload', songid=song.id)) 
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['IMAGE_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream, file_ext):
            return "Invalid image", 400
        newname = "{}.image_{}.jpg".format(song.id, str(num))
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], newname))
        mlink = Mlinks(filename=filename, mtype=mtype, murl=newname)
        db.session.add(mlink)
        song.media.append(mlink)
        db.session.add(song)
        db.session.commit()
    return '', 204
    

@app.route('/uploads_i/<filename>')
@login_required
def upload_i(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    delete_form = EmptyForm()
    if delete_form.submit:
        id = request.args.get('id', type=int)
        song = Song.query.get_or_404(id)
        mlinkid = request.args.get('mlinkid', type=int)
        mlink = Mlinks.query.get(mlinkid)
        # mtype = request.args.get('mtype', type=int)
        song.media.remove(mlink)
        if mlink.mtype > 1:
            if os.path.isfile(app.config['UPLOAD_PATH'] + mlink.murl):
                os.remove(os.path.join(app.config['UPLOAD_PATH'], mlink.murl))       
        db.session.delete(mlink)
        db.session.add(song)
        db.session.commit()
        return redirect(url_for('manage_media', id=id))                 
    else:
        flash("There is no link")
        return '', 204
    
    

@app.route('/manage_media', methods=['GET', 'POST'])
@login_required
def manage_media():
    id = request.args.get('id', type=int)
    song = Song.query.get_or_404(id)
    media = song.media.all()
    video_form = AddMedia()
    delete_form = EmptyForm()
    types = ['', 'Youtube', 'Audio', 'Images', 'Other']
    if request.method == 'POST' and video_form.submit():
        ml = Mlinks(filename = video_form.name.data, mtype = 1, murl = video_form.murl.data)
        db.session.add(ml)
        db.session.commit()
        song.media.append(ml)
        db.session.add(song)
        db.session.commit()
        flash("A new link {} has been added".format(ml.filename))
        return redirect(url_for('manage_media', id=id))  
    # if form.submit():
    #     mlinkid = request.args.get('mlinkid', type=int)
    #     mlink = Mlinks.query.get_or_404(mlinkid)
    #     delete_link(mlink, song)
    #     return redirect(url_for('manage_media', id=id))
    return render_template('manage_media.html', video_form=video_form, delete_form=delete_form, song=song, media=media, types=types)

@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    form = EmptyForm() # to delete events
    events = Lists.query.all()
    for e in events:
        date = datetime.now()
        if e.date_end < date:  # ISSUE: Nonetype and datetime are not comparable
            e.status = 2
            db.session.add(e)
            db.session.commit()
    active_events = Lists.query.filter(Lists.status!=2).all()
    # check if date is passed
    if request.method == 'POST':
        cl = Lists(request.form['date'], request.form['title'])
        db.session.add(cl)
        db.session.commit()
    return render_template('calendar.html', form=form, active_events=active_events)  

@app.route('/make_list', methods=['GET', 'POST'])
@login_required
def make_list():
    form = AddEvent()
    if form.validate_on_submit():
        event = Lists(list_title=form.list_title.data, 
                      date_time=form.date_time.data, 
                      date_end=form.date_end.data,
                      mlink=form.mlink.data, creator=current_user)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('.calendar'))
    return render_template('make_list.html', form=form)  

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    songid = request.args.get('songid', type=int)
    song = Song.query.get_or_404(songid)
    cart = [c for c in current_user.cart]
    cartitem = ListItem(title=song.title, desired_key=song.key, listorder=len(cart)+1)
    cartitem.song.append(song)
    current_user.cart.append(cartitem)
    db.session.add(cartitem)
    db.session.add(current_user)
    db.session.commit()
    # need to finish
    return redirect(url_for('songbook'))

@app.route('/cart/<username>', methods=['GET', 'POST'])
@login_required
def cart(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = User.query.all()
    form = EmptyForm()
    e_form = EmptyForm()
    unroleform = EmptyForm()
    deleteform = EmptyForm()
    # songlist = [item for item in user.cart.sort(key=lambda x: x.listorder)]
    sl = sorted(user.cart, key=lambda x: x.listorder)
    songlist = [item for item in sl]
    for l in songlist:
        if l.listorder is None:
            l.listorder = l.id
            db.session.add(l)
            db.session.commit()
    
    return render_template('cart.html', songlist=songlist, form=form, deleteform=deleteform, keyset=keyset, users=users, e_form=e_form, unroleform=unroleform) 

@app.route('/empty_cart', methods=['POST'])    
@login_required
def empty_cart():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    e_form = EmptyForm()
    if e_form.submit():     
        for item in user.cart:
            if item.role is not None:
                empty = []
                item.role = empty
            user.cart.remove(item)
            db.session.delete(item)
        db.session.commit()
        
        return redirect(url_for('cart', username=current_user.username))

@app.route('/delete_item', methods=['POST'])    
@login_required
def delete_item():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    item = request.args.get('item', type=int)
    # user = User.query.filter_by(id=current_user.id).first_or_404()
    deleteform = EmptyForm()
    if deleteform.submit():
        listitem = ListItem.query.get(item)
        order = listitem.listorder
        song = [s for s in listitem.song]
        for s in song:
            listitem.song.remove(s)
            user.cart.remove(listitem)
        for item in user.cart:
            x = item.listorder - order
            if x > 0:
                y = item.listorder - 1
                item.listorder = y
                db.session.add(item)
        db.session.add(listitem)                
        db.session.add(user)
        db.session.delete(listitem)
        db.session.commit()
        return redirect(url_for('cart', username=current_user.username))

@app.route('/unsign_from_cartitem', methods=['POST'])
@login_required    
def unsign_from_cartitem():
    listitemid = request.args.get('itemid', type=int)
    username = request.args.get('username', type=str)
    listitem = ListItem.query.get_or_404(listitemid)
    user = User.query.filter_by(username=username).first_or_404()
    listitem.role.remove(user)
    db.session.add(listitem)
    db.session.commit()
    return redirect(url_for('cart', username=current_user.username))

#update order of list
# using j    
@app.route('/cart_update-list-order', methods=['POST'])
@login_required
def cart_update_list_order():
    order = request.form.getlist('order[]')  
    for index, item_id in enumerate(order, start=1):
        listitem = ListItem.query.get(item_id)
        listitem.listorder = index
        db.session.add(listitem)
    db.session.commit()
    return redirect(url_for('cart', username=current_user.username))
    #return jsonify({'message': 'List order updated successfully.'})

# update desired key to any key
@app.route('/cart_update-desired-key', methods=['POST'])
@login_required
def cart_update_desired_key():
    item_id = request.form.get('item_id')
    desired_key = int(request.form.get('desired_key'))
    list_item = ListItem.query.get(item_id)
    list_item.desired_key = desired_key
    db.session.add(list_item)
    db.session.commit()
    return redirect(url_for('cart', username=current_user.username))

@app.route('/cart_update-notes', methods=['POST'])
@login_required
def cart_update_notes():
    item_id = request.form.get('item_id')
    notes = request.form.get('notes')
    list_item = ListItem.query.get(item_id)
    list_item.notes = notes
    db.session.commit()

    # Return a success response
    return redirect(url_for('cart', username=current_user.username))

@app.route('/cart_assign-user', methods=['POST'])
@login_required
def cart_assign_user():
    item_id = request.form.get('item_id')
    user_id = request.form.get('user_id')

    # Retrieve the corresponding list item from the database
    listitem = ListItem.query.get(item_id)

    # Retrieve the user from the database based on the provided user_id
    user = User.query.filter_by(id=user_id).first_or_404()
    if user not in listitem.role:
        listitem.role.append(user)
        db.session.add(listitem)
        db.session.commit()
    else:
        flash("{} is already assigned.".format(user.username))
    # Return a success response
    return redirect(url_for('cart', username=current_user.username))

@app.route('/assign2event', methods=['GET', 'POST'])
@login_required
def assign2event():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    addform = AddEvent()
    assignform = Assign2Event()
    
    if request.method == 'POST':
        if addform.submit():
            event = Lists(list_title=addform.list_title.data, 
                          date_time=addform.date_time.data, 
                          date_end=addform.date_end.data,
                          mlink=addform.mlink.data, creator=current_user)
        elif assignform.submit():
           event_id = assignform.event.data
           event = Lists.query.get_or_404(event_id)
           # if event.items is not None:
        ilist = [it for it in user.cart] # issue if assigning to existing lists. needs fixing
        event.items = ilist
        for i in ilist:
            user.cart.remove(i)
        db.session.add(event)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('calendar'))    # later to redirect to event view
    return render_template('assign2event.html', addform=addform, assignform=assignform) 
    
@app.route('/events')    
def events():    
    events = []
    lists = Lists.query.all()
    for list_item in lists:
        event = {
            'id': list_item.id,
            'title': list_item.list_title,
            'start': list_item.date_time.isoformat(),
            'end': list_item.date_end.isoformat(),
            'url': f'/lists/{list_item.id}',  # Link to the detail page
            'editable': True  # Set to False if you want to disable event editing
        }
        events.append(event)
    return jsonify(events)

@app.route('/delete_event', methods=['POST'])
@login_required    
def delete_event(): 
    return redirect(url_for('.calendar'))
                    
@app.route('/edit_event/<listid>', methods=['GET', 'POST'])
@login_required
def edit_event(listid):
    event = Lists.query.get_or_404(listid)
    form = AddEvent()
    # assignform = assign multiple users to this event
    if form.validate_on_submit():
        event.list_title=form.list_title.data 
        event.date_time=form.date_time.data 
        event.date_end=form.date_end.data
        event.mlink=form.mlink.data
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('.lists', listid=event.id))
    elif request.method == 'GET':
        form.list_title.data = event.list_title
        form.date_time.data = event.date_time
        form.date_end.data = event.date_end
        form.mlink.data = event.mlink
    return render_template('edit_event.html', form=form)  

#vivew event - need to change later from lists to view_event. on the next db flush
@app.route('/lists/<listid>')
@login_required    
def lists(listid):    
    event = Lists.query.get_or_404(listid)
    users = User.query.all()
    user = User.query.get_or_404(event.user_id)
    form = EmptyForm()
    unroleform = EmptyForm()
    de_form = EmptyForm()
    deleteform = EmptyForm()
    sl = sorted(event.items, key=lambda x: x.listorder)
    songlist = [item for item in sl]
    
    return render_template('event_detail.html', event=event, songlist=songlist, form=form, deleteform=deleteform, keyset=keyset, users=users, user=user, de_form=de_form, unroleform=unroleform) 

@app.route('/unsign_from_listitem', methods=['POST'])
@login_required    
def unsign_from_listitem():
    listitemid = request.args.get('itemid', type=int)
    username = request.args.get('username', type=str)
    listitem = ListItem.query.get_or_404(listitemid)
    user = User.query.filter_by(username=username).first_or_404()
    listid = listitem.list_id
    listitem.role.remove(user)
    db.session.add(listitem)
    db.session.commit()
    return redirect(url_for('lists', listid=listid))

@app.route('/list_delete_item', methods=['POST'])    
@login_required
def list_delete_item():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    item = request.args.get('item', type=int)
    listid = request.args.get('listid', type=int)
    event = Lists.query.get_or_404(listid)
    # user = User.query.filter_by(id=current_user.id).first_or_404()
    deleteform = EmptyForm()
    if deleteform.submit():
        listitem = ListItem.query.get(item)
        order = listitem.listorder
        song = [s for s in listitem.song]
        for s in song:
            listitem.song.remove(s)
            empty = []
            listitem.role = empty
            event.items.remove(listitem)
        for item in event.items:
            x = item.listorder - order
            if x > 0:
                y = item.listorder - 1
                item.listorder = y
                db.session.add(item)
        db.session.add(listitem)
        db.session.add(event)                
        db.session.add(user)
        db.session.delete(listitem)
        db.session.commit()
        return redirect(url_for('lists', listid=listid))

#update order of list
# using j    
@app.route('/list_update-list-order', methods=['POST'])
@login_required
def list_update_list_order():
    order = request.form.getlist('order[]')  
    for index, item_id in enumerate(order, start=1):
        listitem = ListItem.query.get(item_id)
        listid = listitem.list_id
        listitem.listorder = index
        db.session.add(listitem)
    db.session.commit()
    return redirect(url_for('lists', listid=listid))
    #return jsonify({'message': 'List order updated successfully.'})

# update desired key to any key
@app.route('/list_update-desired-key', methods=['POST'])
@login_required
def list_update_desired_key():
    item_id = request.form.get('item_id')
    desired_key = int(request.form.get('desired_key'))
    listitem = ListItem.query.get(item_id)
    listid = listitem.list_id
    listitem.desired_key = desired_key
    db.session.add(listitem)
    db.session.commit()
    return redirect(url_for('lists', listid=listid))

@app.route('/list_update-notes', methods=['POST'])
@login_required
def list_update_notes():
    item_id = request.form.get('item_id')
    notes = request.form.get('notes')
    listitem = ListItem.query.get(item_id)
    listid = listitem.list_id
    listitem.notes = notes
    db.session.commit()
    return redirect(url_for('lists', listid=listid))

@app.route('/list_assign-user', methods=['POST'])
@login_required
def list_assign_user():
    item_id = request.form.get('item_id')
    user_id = request.form.get('user_id')

    # Retrieve the corresponding list item from the database
    listitem = ListItem.query.get(item_id)
    listid = listitem.list_id
    # Retrieve the user from the database based on the provided user_id
    user = User.query.filter_by(id=user_id).first_or_404()
    if user not in listitem:
        listitem.role.append(user)
        db.session.add(listitem)
        db.session.commit()
    else:
        flash("{} is already assigned.".format(user.username))
    # Return a success response
    return redirect(url_for('lists', listid=listid))

@app.route('/tagging', methods=['POST'])
@login_required
def tagging():
    songid = request.args.get('id', type=int)
    song = Song.query.filter_by(id=songid).first_or_404()
    tags_form = TagsForm(obj=song)
    if request.method == "POST" and tags_form.submit():
        tagged_list = ([tagged for tagged in song.tags])
        # selected_tags = request.form['name']
        selected_tags = request.form.getlist('name')  # Use getlist() to retrieve multiple checkbox values
        selected_tags = list(map(int, selected_tags))
        #first remove untagged tags
        for tg in tagged_list:
            if tg not in selected_tags:
                song.tags.remove(tg)
        
        #add new tagged tags
        for tag_id in selected_tags:
            t = Tag.query.get(tag_id)
            if t is not None and t not in tagged_list:
                song.tags.append(t)
        db.session.add(song)
        db.session.commit()
        flash("Tags have been updated.")
    else:
        flash('Issues: Validation not passed.')
    return redirect(url_for('.view_song', id=song.id, key=song.key))


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