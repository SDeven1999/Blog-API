from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app, database, migrations, and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'  # Use MySQL/Postgres in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    posts = db.relationship('Post', backref='author', lazy=True)

# Blog post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Login manager callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes for user authentication and blog posts

# Home page - List of blog posts with pagination
@app.route('/')
def homepage():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts)

# View a single post
@app.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', post=post)

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('homepage'))

        flash('Login failed. Check your credentials and try again.', 'danger')

    return render_template('login.html')

# User logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))

# Create a new blog post
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author=current_user)
        db.session.add(new_post)
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('homepage'))

    return render_template('create_post.html')

# Edit an existing blog post
@app.route('/post/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        flash('You are not authorized to edit this post', 'danger')
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', id=post.id))

    return render_template('edit_post.html', post=post)

# Delete a blog post
@app.route('/post/delete/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        flash('You are not authorized to delete this post', 'danger')
        return redirect(url_for('homepage'))

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('homepage'))

if __name__ == '__main__':
    app.run(debug=True)
