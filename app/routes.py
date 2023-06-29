from flask import render_template, flash, redirect, url_for, request, abort, send_from_directory, jsonify, session, g
from app import app, db, validate_image, validate_audio
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddSong, EditSong, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, Transpose
from app.forms import AddTag, TagsForm, SongsForm, AddMedia, AddEvent, Assign2Event, SearchForm
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Song, Post, Tag, Mlinks, Lists, ListItem, eventitems
from datetime import datetime
from app.email import send_password_reset_email
from app.core import Chordpro_html, Html_columns
from werkzeug.utils import secure_filename
from functools import wraps
from langdetect import detect, LangDetectException
from app.translate import translate
import os
from flask_babel import _, get_locale
from sqlalchemy.orm import joinedload
#import logging

# mtype 1 - Youtube  2 -Audio   3 - images 4 - 'Other'
keyset = ('Empty', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
lang = ('None', 'Eng', 'Kor', 'Rus')

# splits text into two columns 
def split_text(text, viewtype, ori_key_int, transpose):
    lyrics = ""
    lines = text.split('\n')
    first_part = []
    second_part = []
    count = 0
    half_total = len(lines)/2
    
    
    for line in lines:
        if count < half_total:
            first_part.append(line)
        else:
            if line.strip() == '':
                second_part.append(line)
                second_part.extend(lines[count+1:])
                break
            else:
                first_part.append(line)
        count += 1
    
    first = '\n'.join(first_part) 
    second = '\n'.join(second_part)
    
    if viewtype == 1:
        html1 = Chordpro_html(first, 1, ori_key_int, transpose)
        html2 = Chordpro_html(second, 1, ori_key_int, transpose)
    elif viewtype ==2:
        html1 = Chordpro_html(first, False, 0, 0)
        html2 = Chordpro_html(second, False, 0, 0)
    
    lyrics = '<div class="row"><div class="col-auto">&nbsp;</div><div class="col-5">{}</div><div class="col-5"><br><br><br><br><br>{}</div></div>'.format(html1, html2)
    
    return lyrics
    # lines = text.split('\n')
    # first_part = '\n'.join(lines[:20])
    # second_part = '\n'.join(lines[20:])
    # return first_part, second_part


    # lines = text.split('\n')
    # if len(lines) <= 20:
    #     return text, ''
    # else:
    #     first_part = '\n'.join(lines[:20])
    #     for i in range(20, len(lines)):
    #         if lines[i].strip() == '':
    #             second_part = '\n'.join(lines[i+1:])
    #             return first_part, second_part
    #     return first_part, ''

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

@app.route('/language=<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(url_for('index'))

@app.route('/search')
def search():
    # for adding into cart
    keyword = request.args.get('query')
    results = Song.query.msearch(keyword,fields=['title', 'singer', 'lyrics'])
    c = 2
    tags = Tag.query.all()
    form = EmptyForm()
    # search form
    # results = []
    # searchform = SearchForm()
    # if searchform.validate_on_submit():
    #     search = searchform.search.data
    #     results = Song.query.filter(Song.title.like("%"+search+"%")).all()
    #     return redirect('search.html', resutls=results)
    #     # to add chosen song to the cart {{ url_for('.add_to_cart', songid=song.id) }}
    return render_template('search.html', title=_('Search results'), form=form, results=results, keyword=keyword, keyset=keyset, lang=lang, tags=tags, c=c)


@app.route('/uploads/audio/<filename>')
def uploads_folder(filename):
    return send_from_directory(app.config['AUPLOAD_PATH'], filename)

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.locale = str(get_locale())

@app.route('/explore')
@login_required
def explore():
    # page = request.args.get('page', 1, type=int)
    fulllist = Lists.query.all()
    new_songs = Song.query.order_by(Song.timestamp.desc()).limit(10).all()
    events = Lists.query.filter(Lists.date_time > datetime.utcnow()).order_by(Lists.date_time.desc()).all()
    o_events = Lists.query.filter(Lists.date_time < datetime.utcnow()).order_by(Lists.date_time.desc()).all()
    itemqty = {}
    for event in fulllist:
        itemqty[event.id] = len([ll for ll in event.items])
    # posts = Post.query.order_by(Post.timestamp.desc()).paginate(
    #     page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    # next_url = url_for('explore', page=posts.next_num) \
    #     if posts.has_next else None
    # prev_url = url_for('explore', page=posts.prev_num) \
    #     if posts.has_prev else None
    return render_template('explore.html', title=_('Explore'), 
                           events=events, o_events=o_events, itemqty=itemqty, new_songs=new_songs, keyset=keyset)

@app.route('/process-lyrics', methods=['POST'])
def process_lyrics():
    lyrics = request.form.get('lyrics')
    showchords = int(request.form.get('showchords'))
    ori_key_int = int(request.form.get('ori_key_int'))
    transpose = int(request.form.get('transpose'))
    # Call Chordpro_html function with the provided data
    html = Chordpro_html(lyrics, showchords, ori_key_int, transpose)
    # Return the processed result
    return html


@app.route('/onstage')
def onstage():
    eventid = request.args.get('eventid', type=int)
    viewtype = request.args.get('viewtype', type=int) # if 1 show with chords if 2 show without chords 3 show images
    event = Lists.query.get_or_404(eventid)
    # songs = event.items.all()
    # list_obj = ListItem.query.join(Lists.items).filter(Lists.id == eventid).order_by(ListItem.listorder).all()
    # media = Mlinks.query.join(Song.media).filter(Song.id=)
    unsorted = sorted(event.items, key=lambda x: x.listorder)
    songlist = [item for item in unsorted]
    transpose = 0
    lyrics = []
    mlinks_check = []
    music_sh = []
    my_dict = {}
    if not unsorted:
        flash(_('Error, there are no items in this event.'))
        return redirect('lists', listid=eventid)
    if not viewtype:
        flash(_('Error, view condition is not defined.'))
        return redirect('lists', listid=eventid)
    if viewtype < 3:
        for i in unsorted:
            transpose = i.desired_key
            # make sure viewtype has been passed

            for s in i.song:
                ori_key_int = s.key
                if transpose:
                    split = split_text(s.lyrics, viewtype, ori_key_int, transpose)
                else:    
                    split = split_text(s.lyrics, 2, 0, 0)
            lyrics.append(split)
            # if viewtype is 3, then gather as many 
    if viewtype == 3:
        # making a list of booleans if song.media has pictures or not
        index_list = []
        for i in unsorted:
            for s in i.song:
                if not s.media:
                    mlinks_check.append(False)
                else:
                    cntrl = 0
                    for m in s.media:
                        if m.mtype == 3:
                            cntrl=cntrl+1
                    if cntrl > 1:
                        mlinks_check.append(True)
                    else:
                        mlinks_check.append(False)
                break
                    
        # make a list of murls of pictures in a list
        for index, i in enumerate(unsorted):
                       
            index_list.append(index)
            for ss in i.song:
                if mlinks_check[index]:
                    ex = []
                    for ll in ss.media:
                        if ll.mtype ==3:
                            murl = ll.murl
                            ex.append(murl) 
                    music_sh.append(ex)
                elif mlinks_check[index] == False:
                    ori_key_int = ss.key
                    transpose = i.desired_key
                    split = split_text(ss.lyrics, 1, ori_key_int, transpose)
                    music_sh.append(split)         
        # make a dict
        my_dict["id"]= index_list
        my_dict["image"] = mlinks_check
        my_dict["values"] = music_sh 

                   
        # and at the end combine 
    return render_template('stage.html', songlist=songlist, event=event, lyrics=lyrics, viewtype=viewtype, my_dict=my_dict)

    

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    new_songs=[]
    page = request.args.get('page', 1, type=int)
    fulllist = Lists.query.all()
    events = Lists.query.filter(Lists.date_time > datetime.utcnow()).order_by(Lists.date_time.desc()).all()
    o_events = Lists.query.filter(Lists.date_time < datetime.utcnow()).order_by(Lists.date_time.desc()).all()
    itemqty = {}
    for event in fulllist:
        itemqty[event.id] = len([ll for ll in event.items])
    # posts = current_user.followed_posts().paginate(
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home Page'), form=form, posts=posts.items, 
                           next_url=next_url, prev_url=prev_url, events=events, o_events=o_events, itemqty=itemqty, new_songs=new_songs)

@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@app.route('/songbook')
def songbook():
    form = EmptyForm()
    tags = Tag.query.all()
    c = 1
    page = request.args.get('page', 1, type=int)
    songs = Song.query.order_by(Song.title.asc()).paginate(
        page=page, per_page=app.config['SONGS_PER_PAGE'], error_out=False)
    next_url = url_for('songbook', page=songs.next_num) \
        if songs.has_next else None
    prev_url = url_for('songbook', page=songs.prev_num) \
        if songs.has_prev else None
    return render_template('songbook.html', title=_('Songbook'), songs=songs.items, 
                           next_url=next_url, prev_url=prev_url, keyset=keyset, lang=lang, form=form, tags=tags, c=c)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)

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
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html', title=_('Register'), form=form)

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
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)    

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
        flash(_('a new song has been added and saved'))
        return redirect(url_for('songbook'))
    return render_template('add_song.html', title=_('Add a song'), form=form)

@app.route('/tag_list', methods=['GET', 'POST'])
def tag_list():
    form = AddTag()
    untag_form = EmptyForm()
    tags = Tag.query.all()
    if form.validate_on_submit():
        t = Tag(name=form.name.data) 
        db.session.add(t)
        db.session.commit()
        flash(_('A new tag has been saved.'))
        return redirect(url_for('tag_list'))      
    return render_template('tag_list.html', title=_('Tag list'), tags=tags, form=form, untag_form=untag_form)

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
    addform = EmptyForm()
    return render_template('tag_songlist.html', tag=tag, songs=songs.items,
                            next_url=next_url, prev_url=prev_url, form=form, addform=addform)

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
        flash(_('Song has been removed from tag {}.'.format(tag.name)))
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
            flash(_('Song {} not found.'.format(song.title)))
            return redirect(url_for('.view_song', id=id))
        song.tags=[]
        db.session.commit()
        flash(_('All tags for {} have been untagged.'.format(song.title)))
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
            flash(_('Tag {} does not exist.'.format(tag.name)))
            return redirect(url_for('tag_list'))
        if tag.songs is not None:
            t_songs = tag.songs.all()
            for ts in t_songs:
                ts.tags.remove(tag)   
        db.session.delete(tag)
        db.session.commit()
        flash(_('Tag has been unlinked from all songs and removed from Database'))
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
            flash(_('Song {} not found.'.format(song.title)))
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
        flash(_('Song {} is deleted.'.format(song.title)))
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
        flash(_('Changes to the song have been saved.'))
        return redirect(url_for('.view_song', id=song.id, key=key)) #later change it to view song mode
    elif request.method == 'GET':
        form.title.data = song.title
        form.singer.data = song.singer
        form.info.data = song.info
        form.key.data = song.key
        form.language.data = song.language
        form.lyrics.data = song.lyrics
    return render_template('edit_song.html', title=_('Edit Song'), form=form) 

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
            flash(_('Song {} or {} not found.'.format(cur_song.title, tr_song.title)))
            return redirect(url_for('songbook'))
        if cur_song.language == tr_song.language:
            flash(_('You cannot link songs of same language!'))
            return redirect(url_for('.view_song', id=cur_song.id))
        # cur_song.add_transl(tr_song)
        cur_song.translated.append(tr_song)
        db.session.add(cur_song)
        db.session.commit()
        flash(_('The song {} now has a translated song {}.'.format(cur_song.title, tr_song.title)))
        return redirect(url_for('.view_song', id=id))
    else:
        flash(_('Issues: Validation not passed.'))
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
            flash(_('Song {} or {} not found.'.format(cursong.title, selsong.title)))
            return redirect(url_for('.view_song', id=cursong.id))
        if selsong not in cursong.translated:
            flash(_('Current song does not have a link with selected song!'))
            return redirect(url_for('.view_song', id=cursong.id))
        # cur_song.add_transl(tr_song)
        cursong.translated.remove(selsong)
        db.session.add(cursong)
        db.session.commit()
        flash(_('The song {} and  song {} are now not linked.'.format(cursong.title, selsong.title)))
        return redirect(url_for('.view_song', id=cursong.id))
    else:
        flash(_('Issues: Validation not passed.'))
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
    files = os.listdir(app.config['UPLOAD_PATH'])
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
        ori_key = ori_key + _(" | transposed to ") + keyset[transpose]
    showchords = True
    html = Chordpro_html(lyrics, showchords, ori_key_int, transpose)
    only_lyrics = Chordpro_html(lyrics, False, 0, 0)
    if song is None:
        flash(_('Current song does not have lyrics'))
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
        return render_template('view_song.html', title=_('View Song'), html=html, transl_form=transl_form, 
                               remove_transl_form=remove_transl_form, delete_form=delete_form, tagged_list=tagged_list, 
                               tag_states=tag_states, tags_form=tags_form, only_lyrics=only_lyrics, song=song, form=form, 
                               ori_key=ori_key, t_songlist=t_songlist, lang=lang, untagall_form=untagall_form, media=media, files=files)

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
        flash(_('type variable is None.'))
        return redirect(url_for('.view_song', songid=song.id)) 
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

@app.route('/upload_audio', methods=['POST'])
@limit_content_length(50 * 1024 * 1024)
def upload_audio():
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
        flash(_('type variable is None.'))
        return redirect(url_for('.view_song', songid=song.id)) 
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # if file_ext not in app.config['AUDIO_EXTENSIONS'] or file_ext != validate_audio(uploaded_file.stream, file_ext):
        if file_ext not in app.config['AUDIO_EXTENSIONS']:
            return "Invalid audio", 400
        newname = "{}.audio_{}{}".format(song.id, str(num), file_ext)
        uploaded_file.save(os.path.join(app.config['AUPLOAD_PATH'], newname))
        mlink = Mlinks(filename=filename, mtype=mtype, murl=url_for('uploads_folder', filename=newname))
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
        flash(_("A new link {} has been added".format(ml.filename)))
        return redirect(url_for('manage_media', id=id))  
    return render_template('manage_media.html', video_form=video_form, delete_form=delete_form, song=song, media=media, types=types)

@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    form = EmptyForm() # to delete events
    events = Lists.query.all()
    for e in events:
        date = datetime.now()
        if e.date_end and e.date_end < date:  # ISSUE: Nonetype and datetime are not comparable
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
    c = request.args.get('c', type=int)
    keyword = request.args.get('keyword', type=str)
    if c != 2:
        keyword = ''
    user = User.query.filter_by(username=current_user.username).first_or_404()
    song = Song.query.get_or_404(songid)
    cart = [c for c in current_user.cart]
    cartitem = ListItem(title=song.title, desired_key=song.key, listorder=len(cart)+1)
    cartitem.song.append(song)
    user.cart.append(cartitem)
    db.session.add(cartitem)
    db.session.add(user)
    db.session.commit()
    # need to finish
    if c == 1:
        return redirect(url_for('songbook'))
    if c == 2:
        return redirect(url_for('search', query=keyword))
    else:
        return redirect(url_for('explore'))

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
            # db.session.add(l)
        db.session.commit()
    return render_template('cart.html', songlist=songlist, form=form, deleteform=deleteform, keyset=keyset, users=users, e_form=e_form, unroleform=unroleform) 

@app.route('/empty_cart', methods=['POST'])    
@login_required
def empty_cart():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    cart = [c for c in user.cart]
    e_form = EmptyForm()
    if e_form.submit():     
        for item in cart:
            if item.role is not None:
                empty = []
                item.role = empty
            user.cart.remove(item)
            db.session.add(user)
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
        flash(_("{} is already assigned.".format(user.username)))
    # Return a success response
    return redirect(url_for('cart', username=current_user.username))

@app.route('/assign2event', methods=['GET', 'POST'])
@login_required
def assign2event():
    addform = AddEvent()
    assignform = Assign2Event()       
    return render_template('assign2event.html', addform=addform, assignform=assignform) 

@app.route('/add2event', methods=['POST'])
@login_required
def add2event():
    addform = AddEvent()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    if addform.validate_on_submit():
        event = Lists(list_title=addform.list_title.data, date_time=addform.date_time.data, date_end=addform.date_end.data, mlink=addform.mlink.data, creator=current_user)
        for i in user.cart:
            event.items.append(i)
        empty=[]
        user.cart = empty
        db.session.add(event)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('calendar'))    # later to redirect to event view    
    else:
        flash(_("Unable to create event or add to new event."))
    # Return a success response
    return redirect(url_for('cart', username=current_user.username)) 
        
@app.route('/add2xevent', methods=['POST'])
@login_required
def add2xevent():    
    assignform = Assign2Event()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    if assignform.validate_on_submit():
        event_id = assignform.event.data
        event = Lists.query.get_or_404(event_id)
        print(event.list_title)
        # if event.items is not None:
        
        for i in user.cart:
            event.items.append(i)
        for test in event.items:
            print(test.title)
        db.session.add(event)
        empty=[]
        user.cart = empty
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('calendar'))    # later to redirect to event view
    else:
        flash(_("Unable to add list to existing event."))
    # Return a success response
    return redirect(url_for('cart', username=current_user.username)) 
    
@app.route('/events')    
def events():    
    events = []
    lists = Lists.query.all()
    for list_item in lists:
        event = {
            'id': list_item.id,
            'title': list_item.list_title,
            'start': list_item.date_time.isoformat() if list_item.date_time else None,
            'end': list_item.date_end.isoformat() if list_item.date_end else None,
            'url': '/lists/{}'.format(list_item.id),  # Link to the detail page
            'editable': True  # Set to False if you want to disable event editing
        }
        events.append(event)
    return jsonify(events)

@app.route('/delete_event', methods=['POST'])
@login_required    
def delete_event(): 
    eventid = request.args.get('eventid', type=int)
    jump = request.args.get('jump', type=str)
    de_form = EmptyForm()
    if jump is None:
        jump = "calendar"
    if de_form.submit():
        l = Lists.query.get_or_404(eventid)
        for item in l.items:
            l.items.remove(item)
            db.session.delete(item)
        db.session.delete(l)
        db.session.commit()
        return redirect(url_for('{}'.format(jump)))
    return redirect(url_for('calendar'))
                    
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
    event = listitem.list.first()
    listid = event.id
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
        flash(_("{} is already assigned.".format(user.username)))
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
        flash(_("Tags have been updated."))
    else:
        flash(_('Issues: Validation not passed.'))
    return redirect(url_for('.view_song', id=song.id, key=song.key))


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User {} not found.'.format(username)))
            return redirect(url_for('index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following {}!'.format(username)))
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
            flash(_('User {} not found.'.format(username)))
            return redirect(url_for('index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following {}.'.format(username)))
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
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title=_('Reset Password'), form=form)

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
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)