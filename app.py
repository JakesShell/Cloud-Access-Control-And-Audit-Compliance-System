from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from io import BytesIO
from datetime import datetime
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app = Flask(__name__, template_folder=BASE_DIR)
app.config["SECRET_KEY"] = "change-this-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'users.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

FERNET_KEY = b"8bQ1aNHz9v2H8Mln4Q6K0AH4K3X4mTkh5B0k0e1W6dY="
fernet = Fernet(FERNET_KEY)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class FileRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def ensure_upload_folder():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/styles.css")
def static_files():
    return send_file(os.path.join(BASE_DIR, "styles.css"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("That username is already taken.", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/home")
@login_required
def home():
    files = (
        FileRecord.query.filter_by(owner_id=current_user.id)
        .order_by(FileRecord.uploaded_at.desc())
        .all()
    )
    return render_template("home.html", files=files)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        uploaded_file = request.files.get("file")

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please choose a file to upload.", "error")
            return redirect(url_for("upload"))

        safe_name = secure_filename(uploaded_file.filename)
        if not safe_name:
            flash("Invalid filename.", "error")
            return redirect(url_for("upload"))

        stored_filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{safe_name}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)

        encrypted_data = fernet.encrypt(uploaded_file.read())
        with open(file_path, "wb") as file_handle:
            file_handle.write(encrypted_data)

        record = FileRecord(
            original_filename=safe_name,
            stored_filename=stored_filename,
            owner_id=current_user.id,
        )
        db.session.add(record)
        db.session.commit()

        flash("File uploaded and encrypted successfully.", "success")
        return redirect(url_for("home"))

    return render_template("upload.html")


@app.route("/download/<int:file_id>")
@login_required
def download(file_id):
    record = FileRecord.query.filter_by(id=file_id, owner_id=current_user.id).first_or_404()
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], record.stored_filename)

    if not os.path.exists(file_path):
        flash("File not found on server.", "error")
        return redirect(url_for("home"))

    with open(file_path, "rb") as file_handle:
        encrypted_data = file_handle.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=record.original_filename,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    ensure_upload_folder()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
