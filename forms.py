import werkzeug
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from werkzeug.security import generate_password_hash, check_password_hash


class FormatFormData:
    def __init__(self, raw_form_data):

        self.raw_form_data = raw_form_data

        self.replace_password_with_hashed()


    def hash_password(self) -> str:
        return generate_password_hash(self.raw_form_data.password.data, salt_length=8)

    def replace_password_with_hashed(self):
        self.raw_form_data.password.data = self.hash_password()

    def get_formatted_data(self) -> dict:
        return {field: entry for (field, entry) in self.raw_form_data.data.items() if
                field != "submit" and field != "csrf_token"}


##WTForm

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LET ME IN!")

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP!")



class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("submit comment")