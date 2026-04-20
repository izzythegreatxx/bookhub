from flask import Flask, render_template
import os
from models import db, Book, User
from routes.routes import books_bp
from routes.shelves import shelves_bp
from blocklist import BLOCKLIST
from flask_jwt_extended import JWTManager
from routes.auth import auth_bp
from mail_config import mail


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-secret-key-change-me"



# Database configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Authentication configurations
app.config["JWT_SECRET_KEY"] = "super-secret-key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 900 # 15 minutes
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 2592000 # 30 days
jwt = JWTManager(app)

# mail configurations
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "jislava27@gmail.com"
app.config["MAIL_PASSWORD"] = "odmm grqz hbtv zsyb"
app.config["MAIL_DEFAULT_SENDER"] = app.config["MAIL_USERNAME"]

mail.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(shelves_bp)
db.init_app(app)

with app.app_context():
    db.create_all()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in BLOCKLIST

# Register the blueprint
app.register_blueprint(books_bp)

@app.get("/")
def auth_page():
    return render_template("auth.html")

@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
