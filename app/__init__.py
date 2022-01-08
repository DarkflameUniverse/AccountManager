import os
from flask import Flask, url_for, g, redirect
from functools import wraps
from flask_assets import Environment
from webassets import Bundle
import time
from app.models import db, migrate, PlayKey
from app.schemas import ma
from app.forms import CustomUserManager
from flask_user import user_registered, current_user
from flask_wtf.csrf import CSRFProtect
from app.luclient import query_cdclient, translate_from_locale

from app.commands import init_db, init_accounts
from app.models import Account, AccountInvitation

# Instantiate Flask extensions
csrf_protect = CSRFProtect()
# db and migrate is instantiated in models.py


def create_app():

    app = Flask(__name__, instance_relative_config=True)



    # decrement uses on a play key after a successful registration
    # and increment the times it has been used
    @user_registered.connect_via(app)
    def after_register_hook(sender, user, **extra):
        if app.config["REQUIRE_PLAY_KEY"]:
            play_key_used = PlayKey.query.filter(PlayKey.id == user.play_key_id).first()
            play_key_used.key_uses = play_key_used.key_uses - 1
            play_key_used.times_used = play_key_used.times_used + 1
            db.session.add(play_key_used)
            db.session.commit()

    # A bunch of jinja filters to make things easiers
    @app.template_filter('ctime')
    def timectime(s):
        if s:
            return time.ctime(s) # or datetime.datetime.fromtimestamp(s)
        else:
            return "Never"

    @app.template_filter('check_perm_map')
    def check_perm_map(perm_map, bit):
        if perm_map:
            return perm_map & (1 << bit)
        else:
            return 0 & (1 << bit)

    @app.template_filter('get_zone_name')
    def check_perm_map(zone_id):
        return query_cdclient(
            'select DisplayDescription from ZoneTable where zoneID = ?',
            [zone_id],
            one=True
        )[0]

    @app.template_filter('get_lot_name')
    def get_lot_name(lot_id):
        return query_cdclient(
            'select displayName from Objects where id = ?',
            [lot_id],
            one=True
        )[0]

    @app.template_filter('get_lot_desc')
    def get_lot_desc(lot_id):
        return query_cdclient(
            'select description from Objects where id = ?',
            [lot_id],
            one=True
        )[0]

    @app.template_filter('lu_translate')
    def lu_translate(to_translate):
        return translate_from_locale(to_translate)

    @app.teardown_appcontext
    def close_connection(exception):
        cdclient = getattr(g, '_cdclient', None)
        if cdclient is not None:
            cdclient.close()

    # add the commands to flask cli
    app.cli.add_command(init_db)
    app.cli.add_command(init_accounts)

    register_settings(app)
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
    from .moderation import moderation_blueprint
    app.register_blueprint(moderation_blueprint, url_prefix='/moderation')
    from .log import log_blueprint
    app.register_blueprint(log_blueprint, url_prefix='/log')
    from .bug_reports import bug_report_blueprint
    app.register_blueprint(bug_report_blueprint, url_prefix='/bug_reports')
    from .mail import mail_blueprint
    app.register_blueprint(mail_blueprint, url_prefix='/mail')


def register_settings(app):
    """Register setting from setting and env

    Args:
        app (Flask): Flask app to register for
    """

    # Load common settings
    app.config.from_object('app.settings')

    # Load environment specific settings
    app.config['TESTING'] = False
    app.config['DEBUG'] = False

    # always pull these two from the env
    app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('APP_DATABASE_URI')

    # try to get overides, otherwise just use what we have already
    app.config['USER_ENABLE_REGISTER'] = os.getenv(
        'USER_ENABLE_REGISTER',
        app.config['USER_ENABLE_REGISTER']
    )
    app.config['USER_ENABLE_EMAIL'] = os.getenv(
        'USER_ENABLE_EMAIL',
        app.config['USER_ENABLE_EMAIL']
    )
    app.config['USER_ENABLE_CONFIRM_EMAIL'] = os.getenv(
        'USER_ENABLE_CONFIRM_EMAIL',
        app.config['USER_ENABLE_CONFIRM_EMAIL']
    )
    app.config['REQUIRE_PLAY_KEY'] = os.getenv(
        'REQUIRE_PLAY_KEY',
        app.config['REQUIRE_PLAY_KEY']
    )
    app.config['USER_ENABLE_INVITE_USER'] = os.getenv(
        'USER_ENABLE_INVITE_USER',
        app.config['USER_ENABLE_INVITE_USER']
    )
    app.config['USER_REQUIRE_INVITATION'] = os.getenv(
        'USER_REQUIRE_INVITATION',
        app.config['USER_REQUIRE_INVITATION']
    )
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 2,
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_use_lifo": True
    }
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = os.getenv('MAIL_USE_SSL', 587)
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', False)
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', None)
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', None)
    app.config['USER_EMAIL_SENDER_NAME'] = os.getenv('USER_EMAIL_SENDER_NAME', None)
    app.config['USER_EMAIL_SENDER_EMAIL'] = os.getenv('USER_EMAIL_SENDER_EMAIL', None)


def gm_level(gm_level):
    """Decorator for handling permissions based on the user's GM Level

    Args:
        gm_level (int): 0-9
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.gm_level < gm_level:
                return redirect(url_for('main.index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator
