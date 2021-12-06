import os
from flask import Flask
from flask_assets import Environment
from webassets import Bundle

from app.models import db, migrate
from app.schemas import ma
from flask_wtf.csrf import CSRFProtect

from app.commands import init_db, init_users
from app.models import User, Role, UsersRoles, UserInvitation
from flask_user import user_registered, UserManager


def create_app():

    app = Flask(__name__, instance_relative_config=True)

    secret_key = getenv('SECRET_KEY')
    db_url = getenv('DB_URL')

    # If either of the env variables are not set, attempt to read them from credentials.py.
    if not secret_key or not db_url:
        from credentials import SECRET_KEY, DB_URL

        secret_key = SECRET_KEY
        db_url = DB_URL

    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    # Setup SQL
    db.init_app(app)

    # Setup Login
    login_manager.init_app(app)

    # Setup Bootstrap
    Bootstrap(app)


def register_extensions(app):
    """Register extensions for Flask app

    Args:
        app (Flask): Flask app to register for
    """


def register_extensions(app):
    """Register extensions for Flask app

    Args:
        app (Flask): Flask app to register for
    """