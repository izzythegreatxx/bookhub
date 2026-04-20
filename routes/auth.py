from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from blocklist import BLOCKLIST
from mail_config import mail
from models import User, db

auth_bp = Blueprint("auth", __name__)


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


@auth_bp.post("/auth/register")
def register():
    data = get_json_payload()
    if data is None:
        return jsonify({"message": "Request body must be valid JSON"}), 400

    email = normalize_email(data.get("email", ""))
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

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


@auth_bp.get("/verify/<token>")
def verify_email(token: str):
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


@auth_bp.post("/auth/login")
def login():
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

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "is_verified": user.is_verified,
            },
        }
    ), 200


@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"message": "User logged out"}), 200


@auth_bp.post("/auth/logout-refresh")
@jwt_required(refresh=True)
def logout_refresh():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"message": "Refresh token revoked"}), 200


@auth_bp.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token}), 200