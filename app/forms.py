from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, RadioField, DateField, DateTimeField 
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from wtforms.widgets import ListWidget, CheckboxInput
from app.models import User, Song, Tags
from sqlalchemy import and_
from app import app, db

app.app_context().push()
db.create_all()

chordnote=[
    (0, 'Empty'),
    (1, 'C'), 
    (2, 'C#'), 
    (3, 'D'),
    (4, 'D#'),
    (5, 'E'),
    (6, 'F'),
    (7, 'F#'),
    (8, 'G'),
    (9, 'G#'),
    (10, 'A'),
    (11, 'A#'),
    (12, 'B')
    ]

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
    
class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    remember_me = BooleanField('Remember Me', render_kw={"class": "form-check", "type": "checkbox"})
    submit = SubmitField('Sign In', render_kw={"class": "btn btn-primary"})
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"class": "form-control"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control"})
    submit = SubmitField('Register', render_kw={"class": "btn btn-primary"})
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
            
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')
    
    # make sure during edit stage the login is not duplicated
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.') 

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    #this class is for RadioField, issues with validation
# class FieldsRequiredForm(FlaskForm):
#     class Meta:
#         def render_field(self, field, render_kw):
#             render_kw.setdefault('required', True)
#             return super().render_field(field, render_kw)
               
class AddSong(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    singer = StringField('Singer')
    info = TextAreaField('Information')
    key = SelectField('Key', coerce=int, choices=chordnote)
    language = SelectField('Language', coerce=int, choices=[(1, 'eng'), (2, 'kor'), (3, 'rus')])
    lyrics = TextAreaField('Lyrics', validators=[DataRequired()])
    submit = SubmitField('Save')
    
    def validate_song(self, title, singer):
        song_title = Song.query.filter(and_(Song.title == title, Song.singer == singer))
        if song_title is not None:
            raise ValidationError('Please use a different combination of title and singer.')


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

# class SelectGenre(FlaskForm):
#     genre = MultiCheckboxField('Genre', coerce=int, choices=[(1, "Fast"), (2, "Slow"), (3, "Average")])
#     submit = SubmitField("Save")

class Transpose(FlaskForm):
    key = SelectField('Chord key:', coerce=int, choices=chordnote)
    submit = SubmitField('Transpose')
            
class EditSong(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    singer = StringField('Singer')
    info = TextAreaField('Information')
    key = SelectField('Key', coerce=int, choices=chordnote)
    language = SelectField('Language', coerce=int, choices=[(1, 'eng'), (2, 'kor'), (3, 'rus')])
    lyrics = TextAreaField('Lyrics', validators=[DataRequired()])
    submit = SubmitField('Save')
    
    def validate_song(self, title, singer):
        song_title = Song.query.filter(and_(Song.title == title, Song.singer == singer))
        if song_title is not None:
            raise ValidationError('Please use a different combination of title and singer.')
            
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
    
class AddSermon(FlaskForm):
    date_time = DateTimeField('Date and Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    sermon_title = StringField('Title')
    leader_name = StringField('Leader')
    submit = SubmitField('Set sermon')
    
class EditSermon(FlaskForm):
    date_time = DateField('pickdate')
    sermon_title = StringField('Title')
    leader_name = StringField('Leader')
    submit = SubmitField('Set sermon')

class TagsForm(FlaskForm):
    # tag_list = db.session.query(Tags).all()
    # switches = list(tag_list.items())
    tags = SelectMultipleField('Tags', validators=[DataRequired()])
    submit = SubmitField('Add Tags')
    
    # def __init__(self, *args, **kwargs):
    #     super(TagsForm, self).__init__(*args, **kwargs)
    #     self.tags.choices = [(tag.id, tag.tag) for tag in Tags.query.all()]
    
class AddTag(FlaskForm):
    tag = StringField('Tag', validators=[DataRequired()], render_kw={"class": "form-control"})
    submit = SubmitField('Add a new tag')
    def validate_tag(self, tag):
        tag = Tags.query.filter_by(tag=tag.data).first()
        if tag is not None:
            raise ValidationError('This tag is already in Database.')