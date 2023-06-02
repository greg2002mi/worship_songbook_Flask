from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField, DateTimeField, widgets
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import ListWidget, CheckboxInput, Input
from app.models import User, Song, Tag
from sqlalchemy import and_
from markupsafe import Markup
from wtforms.fields import DateTimeLocalField
# from app import images, audio


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

class DateTimePickerWidget(Input):
    def __init__(self, input_type='datetime-local', **kwargs):
        super().__init__(**kwargs)
        self.input_type = input_type

    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'form-control datetimepicker')
        kwargs.setdefault('autocomplete', 'off')
        kwargs.setdefault('type', self.input_type)
        return super().__call__(field, **kwargs)

class BootstrapListWidget(widgets.ListWidget):
 
    # def __call__(self, field, **kwargs):
    #     kwargs.setdefault("id", field.id)
    #     html = [f"<{self.html_tag} {widgets.html_params(**kwargs)}>"]
    #     for subfield in field:
    #         is_checked = subfield.data in field.data
    #         if self.prefix_label:
    #             html.append(f"<div class='form-check form-switch'>{subfield.label(class_='form-check-label')} {subfield(class_='form-check-input', checked=is_checked)}</div>")
    #         else:
    #             html.append(f"<div class='form-check form-switch'>{subfield(class_='form-check-input', checked=is_checked)} {subfield.label(class_='form-check-label')}</div>")
    #     html.append("</%s>" % self.html_tag)
    #     return Markup("".join(html))
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        html = [f"<{self.html_tag} {widgets.html_params(**kwargs)}>"]
        for subfield in field:
            is_checked = subfield.id in field.id
            id_suffix = f"{subfield.id}"
            if self.prefix_label:
                html.append(f"<div class='form-check form-switch'>{subfield.label(class_='form-check-label', for_=id_suffix)} {subfield(class_='form-check-input', id=id_suffix, checked=is_checked)}</div>")
            else:
                html.append(f"<div class='form-check form-switch'>{subfield(class_='form-check-input', id=id_suffix, checked=is_checked)} {subfield.label(class_='form-check-label', for_=id_suffix)}</div>")
        html.append("</%s>" % self.html_tag)
        return Markup("".join(html))


class MultiCheckboxField(SelectMultipleField):
    widget = BootstrapListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class SongsForm(FlaskForm):
    tr_song_id = SelectField('List of songs', coerce=int, choices=[], validators=[DataRequired()])
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


# class MultiCheckboxField(SelectMultipleField):
#     widget = ListWidget(prefix_label=False)
#     option_widget = CheckboxInput()

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
    name = MultiCheckboxField('Tags', coerce=int)
    submit = SubmitField('Add Tags')
    
    # def __init__(self, *args, **kwargs):
    #     super(TagsForm, self).__init__(*args, **kwargs)
    #     self.tags.choices = [(tag.id, tag.tag) for tag in Tags.query.all()]
    
class AddTag(FlaskForm):
    name = StringField('Tag', validators=[DataRequired()], render_kw={"class": "form-control"})
    submit = SubmitField('Add a new tag')
    def validate_tag(self, name):
        name = Tag.query.filter_by(name=name.data).first()
        if name is not None:
            raise ValidationError('This tag is already in Database.')

# this for saving urls from youtube            
class AddMedia(FlaskForm):
    name = StringField('Title')
    mtype = SelectField('Type of Media', coerce=int, choices=[(1, 'Youtube'), (2, 'mp3'), (3, 'Pictures'), (4, 'Other')])
    murl = StringField('Links or path to media')
    submit = SubmitField('Add media')

class AddEvent(FlaskForm):
    list_title = StringField('Title')
    # date_time = DateTimeField('Set date', format='%Y-%m-%d %H:%M')
    date_time = DateTimeLocalField('Set date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], widget=DateTimePickerWidget())
    # date_end = DateTimeField('End date', format='%Y-%m-%d %H:%M')
    date_end = DateTimeLocalField('End date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], widget=DateTimePickerWidget())
    mlink = StringField('Links or path to media')
    submit = SubmitField('Set event')

# this for uploading images    
# class ImageUpload(FlaskForm):
#     name = StringField('Name', [DataRequired()])
#     image = FileField(validators=[FileAllowed(images, 'Image only!'), FileRequired('Unable to upload empty file!')])
#     submit = SubmitField('Upload')

# class AudioUpload(FlaskForm):
#     name = StringField('Name', [DataRequired()])
#     audio = FileField(validators=[FileAllowed(audio, 'Audio files only!'), FileRequired('Unable to upload empty file!')])
#     submit = SubmitField('Upload')