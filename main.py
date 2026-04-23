'''
Flask application factory for creating and configuring the Flask app
Includes setup for JWT authentication, database initialization, email configuration, and route registration for authentication, book management, and shelf management
'''


import os

from dotenv import load_dotenv

from flask import Flask, render_template
from flask_jwt_extended import JWTManager

from blocklist import BLOCKLIST
from mail_config import mail
from models import db
from routes.auth import auth_bp
from routes.routes import books_bp
from routes.shelves import shelves_bp

# load environment variables from .env file
load_dotenv()


# Factory function to create and configure the Flask application
def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///books.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 900
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 2592000

    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", app.config["MAIL_USERNAME"])

# Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    mail.init_app(app)
    
    # Check if a JWT token is revoked (i.e., in the blocklist)
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
     
    # Register blueprints for authentication, book management, and shelf management
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp, url_prefix="/books")
    app.register_blueprint(shelves_bp, url_prefix="/shelves")
    
    # Define routes for the home page (authentication) and dashboard
    @app.get("/")
    def auth_page():
        return render_template("auth.html")

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)