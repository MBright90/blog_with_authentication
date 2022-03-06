from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, CreateUserForm, LoginForm, CreateComment
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size='100',
                    default='retro',
                    rating='g',)


# *** # CONNECT TO BLOG DB # *** #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# *** # LOGIN FUNCTIONALITY # *** #
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = current_user.id
        except AttributeError:
            return abort(403)
        else:
            if user_id == 1:
                return f(*args, **kwargs)
            else:
                return abort(403)
    return decorated_function


# *** # DATABASE CLASSES # *** #

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

    # Links the User to any Posts they have written
    posts = relationship('BlogPost', back_populates='author')

    # Links the user to any comments they have written
    comments = relationship('Comment', back_populates='author')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # Links the blog_posts table to the User(author)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')

    # Links the BlogPost to the comments table
    comments = relationship('Comment', back_populates='post')


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)

    # Links the comment to the User(author)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User', back_populates='comments')

    # Links the comment to the associated BlogPost(article) it was written for
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    post = relationship('BlogPost', back_populates='comments')

db.create_all()  # Used to create database. Not required further. #


# *** # WEBSITE ROUTING # *** #


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


# *** # USER LOGIN/OUT AND REGISTRY # *** #


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CreateUserForm()

    if form.validate_on_submit():

        new_user = User()
        new_user.username = form.username.data
        new_user.email = form.email.data
        new_user.password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256')

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect('/')

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account with that email exists.')
            return redirect('login')
        elif not check_password_hash(user.password, form.password.data):
            flash('Incorrect Password.')
            return redirect('login')
        else:
            login_user(user)
            return redirect('/')

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# *** # POST FUNCTIONALITY # *** #


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CreateComment()
    requested_comments = Comment.query.filter_by(post_id=post_id)

    if comment_form.validate_on_submit():
        new_comment = Comment(
            text=comment_form.comment.data,
            post=requested_post,
            author=current_user,
        )
        db.session.add(new_comment)
        db.session.commit()

        return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", post=requested_post, post_comments=requested_comments, comment_form=comment_form)


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete_post/<int:post_id>", methods=['GET', 'POST', 'DELETE'])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/delete_comment/<int:post_id>-<int:comment_id>", methods=['GET', 'POST', 'DELETE'])
def delete_comment(post_id, comment_id):
    comment_to_delete = Comment.query.get(comment_id)
    if current_user.id == comment_to_delete.author.id or current_user.id == 1:
        db.session.delete(comment_to_delete)
        db.session.commit()
    else:
        return abort(403)
    return redirect(url_for('show_post', post_id=post_id))


# *** # FURTHER WEBSITE INFORMATION # *** #


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# *** # WEBSITE ACTIVATION # *** #


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
