from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()], render_kw={"class": "form-control"})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={"class": "form-control"})
    remember_me = BooleanField(_l('Remember Me'), render_kw={"class": "form-check", "type": "checkbox"})
    submit = SubmitField(_l('Sign In'), render_kw={"class": "btn btn-primary"})
    
class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()], render_kw={"class": "form-control"})
    email = StringField(_l('Email'), validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={"class": "form-control"})
    password2 = PasswordField(_l('Repeat password'), validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control"})
    submit = SubmitField(_l('Register'), render_kw={"class": "btn btn-primary"})

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))
            
class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))