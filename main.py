from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import exc
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, CreatePostForm, RegistrationForm, FormatFormData, CommentForm
from flask_gravatar import Gravatar
from wtforms import TextAreaField
from flask_wtf import FlaskForm
from secrets import token_hex
from functools import wraps
from flask_gravatar import Gravatar




##INIT APP
app = Flask(__name__)
login_manager = LoginManager()
app.config['SECRET_KEY'] = 'super-secret-key'
login_manager.init_app(app)
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##INIT GRAVATAR
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

##CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="post_author")
    comment_texts = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    post_comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comment_texts")

    text = db.Column(db.Text, nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="post_comments")



with app.app_context():
    db.create_all()
# ----------------- LOAD USER FUNC --------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# ----------------- ADMIN ONLY DECORATOR --------------- #
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        else:
            return func(*args, **kwargs)
    return wrapper




# ----------------- ROUTES --------------- #
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=('GET', 'POST'))
def register():

    registration_form = RegistrationForm()

    if registration_form.validate_on_submit():

        form_data = FormatFormData(registration_form).get_formatted_data()
        new_user = User(**form_data)

        try:
            db.session.add(new_user)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
            flash("An account with that email already exists")
        else:
            login_user(new_user)

            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=registration_form)


@app.route('/login', methods=('GET', 'POST'))
def login():

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if not user:

            flash("No account with that email exists")

        elif not check_password_hash(user.password, form.password.data):

            flash("Incorrect Password")

        else:

            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=('GET', 'POST'))
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)

    comments = Comment.query.filter_by(post_id=post_id)

    comment_form = CommentForm()

    if comment_form.validate_on_submit():

        if not current_user.is_authenticated:
            flash("You must be logged in to comment on posts")
            return redirect(url_for('login'))

        else:
            new_comment = Comment(text=comment_form.comment_text.data,
                                  comment_author=current_user,
                                  parent_post=requested_post)

        db.session.add(new_comment)
        db.session.commit()


    return render_template("post.html", post=requested_post, comments=comments, form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")



@app.route("/new-post", methods=('GET', 'POST'))
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            post_author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)



@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)



@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
