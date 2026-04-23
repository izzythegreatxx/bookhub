'''Authentication routes for user registration, email verification, login, logout, and token refreshing using Flask, 
   Flask-JWT-Extended, and Flask-Mail. Includes helper functions for token generation and email normalization.
'''
from flask import Blueprint, current_app, jsonify, render_template, request, url_for, session
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

import re

from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from blocklist import BLOCKLIST
from mail_config import mail
from models import User, db

# Blueprint for authentication routes
auth_bp = Blueprint("auth", __name__)

# Helper functions for token generation, email normalization, and JSON payload handling
def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_verification_token(email: str) -> str:
    return get_serializer().dumps(email, salt="email-confirm")


def confirm_verification_token(token: str, expiration: int = 3600) -> str | None:
    try:
        return get_serializer().loads(token, salt="email-confirm", max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None


def get_json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def normalize_email(email: str) -> str:
    return email.strip().lower()

# Route for user registration with email verification
@auth_bp.post("/auth/register")
def register():
    try:
        data = get_json_payload()
        if data is None:
            return jsonify({"message": "Request body must be valid JSON"}), 400
    
        username = data.get("username", "").strip()
        email = normalize_email(data.get("email", ""))
        password = data.get("password", "")

        if not username or len(username) < 3 or len(username) > 20:
            return jsonify({"message": "username must be between 3 and 20 characters"}), 400
    
        if not password or len(password) < 8 or len(password) > 64:
            return jsonify({"message": "password must be at least 8 characters long."}), 400

    
        if not re.match(r"^[A-Za-z0-9_]+$", username):
            return jsonify({"message": "username can only contain letters, numbers, and underscores"}), 400
        # Check if the username is already taken
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 400

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 400

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
    
        # Generate a verification token and send a verification email to the user
        token = generate_verification_token(email)
        verify_url = url_for("auth.verify_email", token=token, _external=True)

        msg = Message(
            subject="Verify your BookHub account",
            recipients=[email],
            body=f"Click the link to verify your BookHub account:\n\n{verify_url}",
        )

        try:
            mail.send(msg)
        except Exception:
            current_app.logger.exception("Failed to send verification email")
            return jsonify(
                {"message": "User created, but verification email could not be sent"}
            ), 201

        return jsonify(
            {"message": "User created. Check your email to verify your account."}
        ), 201
    except Exception:
        current_app.logger.exception("Error during registration")
        return jsonify({"message": "An error occurred during registration"}), 500

# Route for email verification when the user clicks the link in the verification email
@auth_bp.get("/verify/<token>")
def verify_email(token: str):
    try:
        email = confirm_verification_token(token)
        if not email:
            return jsonify({"error": "Invalid or expired token"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.is_verified:
            user.is_verified = True
            db.session.commit()

        return render_template("verified.html")
    except Exception:
        current_app.logger.exception("Error during email verification")
        return jsonify({"message": "An error occurred during email verification"}), 500

# Route for user login that issues JWT access and refresh tokens
@auth_bp.post("/auth/login")
def login():
    try:
        data = get_json_payload()
        if data is None:
            return jsonify({"message": "Request body must be valid JSON"}), 400

        email = normalize_email(data.get("email", ""))
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401

        if not user.is_verified:
            return jsonify({"message": "Email not verified"}), 403
    
        # Generate JWT access and refresh tokens for the authenticated user
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
    
        session['user_email'] = user.email
        session['username'] = user.username

        return jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "is_verified": user.is_verified,
                },
            }
        ), 200
    except Exception:
        current_app.logger.exception("Error during login")
        return jsonify({"message": "An error occurred during login"}), 500

# Route for user logout that revokes the current JWT access token
@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    # Add the token's unique identifier (jti) to the blocklist to revoke it
    BLOCKLIST.add(jti)
    return jsonify({"message": "User logged out"}), 200

# Route for user logout that revokes the current JWT refresh token
@auth_bp.post("/auth/logout-refresh")
@jwt_required(refresh=True)
def logout_refresh():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"message": "Refresh token revoked"}), 200

# Route for refreshing the JWT access token using a valid refresh token
@auth_bp.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token}), 200