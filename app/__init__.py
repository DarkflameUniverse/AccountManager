import os
from flask import Flask, url_for
from flask_assets import Environment
from webassets import Bundle
import time
from app.models import db, migrate, PlayKey
from app.schemas import ma
from app.forms import CustomUserManager
from flask_user import user_registered
from flask_wtf.csrf import CSRFProtect

from app.commands import init_db, init_accounts, init_data
from app.models import Account, AccountInvitation

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

    # decrement uses on a play eky after a successful registration
    # and increment the times it has been used
    @user_registered.connect_via(app)
    def after_register_hook(sender, user, **extra):

        play_key_used = PlayKey.query.filter(PlayKey.id == user.play_key_id).first()
        play_key_used.key_uses = play_key_used.key_uses - 1
        play_key_used.key_uses = play_key_used.times_used + 1
        db.session.add(play_key_used)
        db.session.commit()

    @app.template_filter('ctime')
    def timectime(s):
        return time.ctime(s) # or datetime.datetime.fromtimestamp(s)

    # add the commands to flask cli
    app.cli.add_command(init_db)
    app.cli.add_command(init_accounts)
    app.cli.add_command(init_data)

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
    user_manager = CustomUserManager(
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
    from .play_keys import play_keys_blueprint
    app.register_blueprint(play_keys_blueprint, url_prefix='/play_keys')
    from .accounts import accounts_blueprint
    app.register_blueprint(accounts_blueprint, url_prefix='/accounts')
    from .characters import character_blueprint
    app.register_blueprint(character_blueprint, url_prefix='/characters')
    from .properties import property_blueprint
    app.register_blueprint(property_blueprint, url_prefix='/properties')
