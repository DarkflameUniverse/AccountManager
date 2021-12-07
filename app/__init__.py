import os
from flask import Flask, url_for
from flask_assets import Environment
from webassets import Bundle

from app.models import db, migrate
from app.schemas import ma
from flask_wtf.csrf import CSRFProtect

from app.commands import init_db, init_accounts
from app.models import Account, AccountInvitation
from flask_user import user_registered, UserManager

# Instantiate Flask extensions
csrf_protect = CSRFProtect()
# db and migrate is instantiated in models.py


def create_app():

    app = Flask(__name__, instance_relative_config=True)

    # Load common settings
    app.config.from_object('app.settings')
    # Load environment specific settings

    app.config['TESTING'] = False
    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('APP_DATABASE_URI')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 2,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_use_lifo": True
    }
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['USER_EMAIL_SENDER_NAME'] = os.getenv('USER_EMAIL_SENDER_NAME')
    app.config['USER_EMAIL_SENDER_EMAIL'] = os.getenv('USER_EMAIL_SENDER_EMAIL')

    # add the commands to flask cli
    app.cli.add_command(init_db)
    app.cli.add_command(init_accounts)

    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app):
    """Register extensions for Flask app

    Args:
        app (Flask): Flask app to register for
    """
    db.init_app(app)
    migrate.init_app(app, db)
    csrf_protect.init_app(app)
    ma.init_app(app)
    user_manager = UserManager(
        app, db, Account, UserInvitationClass=AccountInvitation
    )

    assets = Environment(app)
    assets.url = app.static_url_path
    scss = Bundle('scss/site.scss', filters='libsass', output='site.css')
    assets.register('scss_all', scss)


def register_blueprints(app):
    """Register blueprints for Flask app

    Args:
        app (Flask): Flask app to register for
    """

    from .main import main_blueprint
    app.register_blueprint(main_blueprint)
    from .admin import admin_blueprint
    app.register_blueprint(admin_blueprint)
