'''
Flask application factory for creating and configuring the Flask app
Includes setup for JWT authentication, database initialization, email configuration, and route registration for authentication, book management, and shelf management
'''


import os

from dotenv import load_dotenv

from flask import Flask, render_template, flash, session, request
from flask_mail import Message
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required

import logging

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
    
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("bookhub.log")
        ]
    )

    logging.info("BookHub app created and logging initialized.")
    
    # Register blueprints for authentication, book management, and shelf management    # Register blueprints for authentication, book management, and shelf management
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp, url_prefix="/books")
    app.register_blueprint(shelves_bp, url_prefix="/shelves")
    
    

    #initialize JWT manager and database
    jwt = JWTManager(app)
    db.init_app(app)
    mail.init_app(app)
    
    
    # Check if a JWT token is revoked (i.e., in the blocklist)
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
     
    
    # Define routes for the home page (authentication) and dashboard
    @app.get("/")
    def auth_page():
        return render_template("auth.html")

    @app.get("/dashboard")
    def dashboard():
        username = session.get('username', "Guest")
            
        return render_template("dashboard.html", username=username  )
    
    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        message_text = None
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            message_content = request.form.get("message")
            
            if not name or not email or not message_content:
                message_text = "ALl fields are required."
            else:
                msg = Message(
                    subject=f"BookHub Contact from {name}", 
                    sender=email, 
                    recipients=["izzytechdev@gmail.com"],
                    body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_content}"
                )
                try:
                    mail.send(msg)
                    message_text = "Your message has been sent successfully! Thank you for reaching out."
                except Exception:
                    message_text = "An error occurred while sending your message. Please try again later."
        return render_template("contact.html", message_text=message_text)   
        


    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)