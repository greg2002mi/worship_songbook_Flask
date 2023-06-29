from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField, DateTimeField, widgets
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, Regexp
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import ListWidget, CheckboxInput, Input
from app.models import User, Song, Tag, Lists
from sqlalchemy import and_
from markupsafe import Markup
from wtforms.fields import DateTimeLocalField
from datetime import datetime
from flask_babel import lazy_gettext as _l
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
    submit = SubmitField(_l('Submit'))

class SongsForm(FlaskForm):
    tr_song_id = SelectField(_l('List of songs'), coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))
    
class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))
    
class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()], render_kw={"class": "form-control"})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={"class": "form-control"})
    remember_me = BooleanField(_l('Remember Me'), render_kw={"class": "form-check", "type": "checkbox"})
    submit = SubmitField(_l('Sign In'), render_kw={"class": "btn btn-primary"})
    
class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Regexp(regex=r'^[a-z]+$', 
            message=_l("Username must contain only lowercase letters"))], render_kw={"class": "form-control"})
    email = StringField(_l('Email'), validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(min=8), Regexp(regex="^(?=.*[a-zA-Z])(?=.*[!@#$%^&*])(?=.*[0-9])",
            message=_l("Password must contain letters and special symbols"))], render_kw={"class": "form-control"})
    password2 = PasswordField(_l('Repeat password'), validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control"})
    submit = SubmitField(_l('Register'), render_kw={"class": "btn btn-primary"})
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different username.'))
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))
            
class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))
    
    # make sure during edit stage the login is not duplicated
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different username.')) 

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

    #this class is for RadioField, issues with validation
# class FieldsRequiredForm(FlaskForm):
#     class Meta:
#         def render_field(self, field, render_kw):
#             render_kw.setdefault('required', True)
#             return super().render_field(field, render_kw)
               
class AddSong(FlaskForm):
    title = StringField(_l('Title'), validators=[DataRequired()])
    singer = StringField(_l('Singer'))
    info = TextAreaField(_l('Information'))
    key = SelectField(_l('Key'), coerce=int, choices=chordnote)
    language = SelectField(_l('Language'), coerce=int, choices=[(1, 'eng'), (2, 'kor'), (3, 'rus')])
    lyrics = TextAreaField(_l('Lyrics'), validators=[DataRequired()])
    submit = SubmitField(_l('Save'))
    
    def validate_song(self, title, singer):
        song_title = Song.query.filter(and_(Song.title == title, Song.singer == singer))
        if song_title is not None:
            raise ValidationError(_l('Please use a different combination of title and singer.'))


# class MultiCheckboxField(SelectMultipleField):
#     widget = ListWidget(prefix_label=False)
#     option_widget = CheckboxInput()

# class SelectGenre(FlaskForm):
#     genre = MultiCheckboxField('Genre', coerce=int, choices=[(1, "Fast"), (2, "Slow"), (3, "Average")])
#     submit = SubmitField("Save")

class Transpose(FlaskForm):
    key = SelectField(_l('Chord key:'), coerce=int, choices=chordnote)
    submit = SubmitField(_l('Transpose'))
            
class EditSong(FlaskForm):
    title = StringField(_l('Title'), validators=[DataRequired()])
    singer = StringField(_l('Singer'))
    info = TextAreaField(_l('Information'))
    key = SelectField(_l('Key'), coerce=int, choices=chordnote)
    language = SelectField(_l('Language'), coerce=int, choices=[(1, 'eng'), (2, 'kor'), (3, 'rus')])
    lyrics = TextAreaField(_l('Lyrics'), validators=[DataRequired()])
    submit = SubmitField(_l('Save'))
    
    def validate_song(self, title, singer):
        song_title = Song.query.filter(and_(Song.title == title, Song.singer == singer))
        if song_title is not None:
            raise ValidationError(_l('Please use a different combination of title and singer.'))
            
class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))
    
class AddSermon(FlaskForm):
    date_time = DateTimeField(_l('Date and Time'), format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    sermon_title = StringField(_l('Title'))
    leader_name = StringField(_l('Leader'))
    submit = SubmitField(_l('Set sermon'))
    
class EditSermon(FlaskForm):
    date_time = DateField(_l('pickdate'))
    sermon_title = StringField(_l('Title'))
    leader_name = StringField(_l('Leader'))
    submit = SubmitField(_l('Set sermon'))

class TagsForm(FlaskForm):
    name = MultiCheckboxField(_l('Tags'), coerce=int)
    submit = SubmitField(_l('Add Tags'))
    
    # def __init__(self, *args, **kwargs):
    #     super(TagsForm, self).__init__(*args, **kwargs)
    #     self.tags.choices = [(tag.id, tag.tag) for tag in Tags.query.all()]
    
class AddTag(FlaskForm):
    name = StringField(_l('Tag'), validators=[DataRequired()], render_kw={"class": "form-control"})
    submit = SubmitField(_l('Add a new tag'))
    def validate_tag(self, name):
        name = Tag.query.filter_by(name=name.data).first()
        if name is not None:
            raise ValidationError(_l('This tag is already in Database.'))

# this for saving urls from youtube            
class AddMedia(FlaskForm):
    name = StringField(_l('Title'))
    mtype = SelectField(_l('Type of Media'), coerce=int, choices=[(1, 'Youtube'), (2, 'mp3'), (3, 'Pictures'), (4, 'Other')])
    murl = StringField(_l('Links or path to media'))
    submit = SubmitField(_l('Add media'))

class AddEvent(FlaskForm):
    list_title = StringField(_l('Title'))
    # date_time = DateTimeField('Set date', format='%Y-%m-%d %H:%M')
    date_time = DateTimeLocalField(_l('Set date'), format='%Y-%m-%dT%H:%M', validators=[DataRequired()], widget=DateTimePickerWidget())
    # date_end = DateTimeField('End date', format='%Y-%m-%d %H:%M')
    date_end = DateTimeLocalField(_l('End date'), format='%Y-%m-%dT%H:%M', validators=[DataRequired()], widget=DateTimePickerWidget())
    mlink = StringField(_l('Links or path to media'))
    submit = SubmitField(_l('Set event'))

class Assign2Event(FlaskForm):
    event = SelectField(_l('Event'), coerce=int)
    submit = SubmitField(_l('Assign'))
    
    def __init__(self, *args, **kwargs):
        super(Assign2Event, self).__init__(*args, **kwargs)
        self.event.choices = [(event.id, "{}({}) - {}".format(event.date_time.strftime('%Y-%m-%d %H:%M'), 
                              User.query.get_or_404(event.user_id).username, event.list_title)) 
                              for event in Lists.query.filter(Lists.date_time > datetime.utcnow()).all()]

class SearchForm(FlaskForm):
    search = StringField(_l('Search for songs'), validators=[DataRequired(), Length(max=100)])
    submit = SubmitField(_l('Search'))
# this for uploading images    
# class ImageUpload(FlaskForm):
#     name = StringField('Name', [DataRequired()])
#     image = FileField(validators=[FileAllowed(images, 'Image only!'), FileRequired('Unable to upload empty file!')])
#     submit = SubmitField('Upload')

# class AudioUpload(FlaskForm):
#     name = StringField('Name', [DataRequired()])
#     audio = FileField(validators=[FileAllowed(audio, 'Audio files only!'), FileRequired('Unable to upload empty file!')])
#     submit = SubmitField('Upload')