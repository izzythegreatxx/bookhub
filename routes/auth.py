from flask import Blueprint, jsonify, request, current_app, render_template, url_for
from models import db, User
from blocklist import BLOCKLIST
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from itsdangerous import URLSafeTimedSerializer
from mail_config import mail
from flask_mail import Message


auth_bp = Blueprint("auth", __name__)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_verification_token(email):
    serializer = get_serializer()
    return serializer.dumps(email, salt="email-confirm")

# Register
@auth_bp.post("/auth/register")
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email or password is required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Generate verification token
    token = generate_verification_token(email)
    verify_url = url_for("auth.verify_email", token=token, _external=True)

    # Send email
    msg = Message(
        subject="Verify your BookHub account",
        recipients=[email],
        body=f"Click the link to verify your account:\n\n{verify_url}"
    )
    mail.send(msg)

    return jsonify({"message": "User created. Check your email to verify your account."}), 201



# verify
def confirm_verification_token(token, expiration=3600):
    serializer = get_serializer()
    try:
        email = serializer.loads(
            token,
            salt="email-confirm",
            max_age=expiration
        )
    except Exception:
        return None
    return email

@auth_bp.get("/verify/<token>")
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        return jsonify({"error": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.is_verified = True
    db.session.commit()

    return render_template("verified.html")




# Login
@auth_bp.post("/auth/login")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_verified:
        return jsonify({"message": "Email not verified"}), 403

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200


# Logout
@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"message": "user logged out"}), 200

# Logout Refresh
@auth_bp.post("/auth/logout-refresh")
@jwt_required(refresh=True)
def logout_refresh():
    jti = get_jwt()["jti"]
    BLOCKLIST.add(jti)
    return jsonify({"message": "refresh token revoked"}), 200
@auth_bp.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token}), 200

