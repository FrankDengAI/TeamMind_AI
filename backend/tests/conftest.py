"""pytest 配置."""
import sys
from pathlib import Path

import bcrypt
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db
from app.config import Config
from app.models import User


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    DEEPSEEK_ENABLED = False


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.drop_all()
        db.create_all()
        pw = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
        u = User(name="Test", account="pytest_user", password_hash=pw, role="user")
        admin = User(name="Admin", account="pytest_admin", password_hash=pw, role="admin")
        db.session.add_all([u, admin])
        db.session.commit()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
