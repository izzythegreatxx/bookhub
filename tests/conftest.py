# tests/conftest.py
import os
import tempfile

import pytest

from main import create_app
from models import db, User


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["MAIL_SUPPRESS_SEND"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def verified_user(app):
    with app.app_context():
        user = User(email="test@example.com", is_verified=True)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_headers(client, verified_user):
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    data = response.get_json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}