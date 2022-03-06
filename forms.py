from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, EqualTo, Length
from flask_ckeditor import CKEditorField


# *** # WTFORMS # *** #

class CreatePostForm(FlaskForm):
    """Uses WTForms to create a group of fields to allow an admin User to upload a BlogPost object to the database."""
    title = StringField(label="Blog Post Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    img_url = StringField(label="Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Blog Content", validators=[DataRequired()])
    submit = SubmitField(label="Submit Post")


class CreateComment(FlaskForm):
    """Uses WTForms to create a single CKEditor field to allow a User to upload a comment on an article."""
    comment = CKEditorField(label="Comment", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField(label="Share Your Thoughts!")


class CreateUserForm(FlaskForm):
    """Uses WTForms to create a group of fields to register a new user. Validation protocols require the password to
    be confirmed, along with a unique username and a unique email address. """
    username = StringField(label="Username", validators=[DataRequired()])
    email = StringField(label="Email Address", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(label="Validate Password", validators=[EqualTo(fieldname='password')])
    submit = SubmitField(label="Let's Get You Involved")


class LoginForm(FlaskForm):
    """Uses WTForms to create a group of fields to log in a returning user."""
    email = StringField(label="Email Address", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Welcome Back")
