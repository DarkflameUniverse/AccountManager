from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import UserMixin

import logging
from flask_sqlalchemy import BaseQuery
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import OperationalError, StatementError
from time import sleep

# retrying query to work around python trash collector
# killing connections of other gunicorn workers
class RetryingQuery(BaseQuery):
    __retry_count__ = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as ex:
                if "server closed the connection unexpectedly" not in str(ex):
                    raise
                if attempts < self.__retry_count__:
                    sleep_for = 2 ** (attempts - 1)
                    logging.error(
                        "Database connection error: {} - sleeping for {}s"
                        " and will retry (attempt #{} of {})".format(
                            ex, sleep_for, attempts, self.__retry_count__
                        )
                    )
                    sleep(sleep_for)
                    continue
                else:
                    raise
            except StatementError as ex:
                if "reconnect until invalid transaction is rolled back" not in str(ex):
                    raise
                self.session.rollback()


db = SQLAlchemy(query_class=RetryingQuery)
migrate = Migrate()

class PlayKey(db.Model):
    __tablename__ = 'play_keys'
    id = db.Column(db.Integer, primary_key=True)

    key_string = db.Column(
        mysql.CHAR(19),
        nullable=False,
        unique=True
    )

    key_uses = db.Column(
        mysql.INTEGER,
        nullable=False,
        server_default='1'
    )
    created_at = db.Column(
        mysql.TIMESTAMP,
        nullable=False,
        server_default=db.func.now()
    )
    active = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='1'
    )

class Account(db.Model, UserMixin):
    __tablename__ = 'accounts'
    id = db.Column(
        db.Integer(),
        primary_key=True
    )

    name = db.Column(
        db.Text(35),
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.Unicode(255),
        nullable=False,
        server_default=u'',
        unique=True
    )
    email_confirmed_at = db.Column(db.DateTime())

    password = db.Column(
        db.Text(),
        nullable=False,
        server_default=''
    )

    gm_level = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

    locked = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    active = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='1'
    )

    banned = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    play_key_id = db.Column(
        db.Integer(),
        db.ForeignKey(PlayKey.id, ondelete='CASCADE'),
        nullable=False
    )

    play_key = db.relationship(
        'PlayKey',
        backref="accounts",
        passive_deletes=True
    )

    created_at = db.Column(db.DateTime())

    mute_expire = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

    @staticmethod
    def get_user_by_id(*, user_id=None):
        return User.query.filter(user_id == User.id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()
        db.session.refresh(self)

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class AccountInvitation(db.Model):
    __tablename__ = 'account_invites'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)

    # save the user of the invitee
    invited_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey(Account.id, ondelete='CASCADE')
    )

    invited_by_account = db.relationship(
        'Account',
        backref="account_invites",
        passive_deletes=True
    )

    # token used for registration page to
    # identify user registering
    token = db.Column(
        db.String(100),
        nullable=False,
        server_default=''
    )



    @staticmethod
    def get_user_by_id(*, user_id=None):
        return User.query.filter(user_id == User.id).first()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class CharacterInfo(db.Model):
    __tablename__ = 'charinfo'
    id = db.Column(mysql.BIGINT, primary_key=True)

    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(Account.id, ondelete='CASCADE'),
        nullable=False
    )
    account = db.relationship(
        'Account',
        backref="charinfo",
        passive_deletes=True
    )

    name = db.Column(
        db.Text(35),
        nullable=False,
        unique=True
    )

    pending_name = db.Column(
        db.Text(35),
        nullable=False,
        unique=True
    )

    needs_rename = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    prop_clone_id = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0',
        unique=True,
        autoincrement=True
    )

    last_login = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

    permission_map = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

class CharacterXML(db.Model):
    __tablename__ = 'charxml'
    id = db.Column(mysql.BIGINT, primary_key=True)
    xml_data = db.Column(
        db.Text(4294000000),
        nullable=False
    )

class CommandLog(db.Model):
    __tablename__ = 'command_log'
    id = db.Column(db.Integer, primary_key=True)

    character_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    character = db.relationship(
        'CharacterInfo',
        backref="command_log",
        passive_deletes=True
    )

    command =  db.Column(
        mysql.VARCHAR(256),
        nullable=False
    )

class Friends(db.Model):
    __tablename__ = 'friends'
    player_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )

    player = db.relationship(
        'CharacterInfo',
        foreign_keys=[player_id],
        backref="player",
        passive_deletes=True
    )

    friend_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )

    friend = db.relationship(
        'CharacterInfo',
        foreign_keys=[friend_id],
        backref="friend",
        passive_deletes=True
    )

    best_friend = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    id = db.Column(db.Integer, primary_key=True)

    game_id = db.Column(
        mysql.INTEGER(),
        nullable=False,
        server_default='0'
    )

    last_played = db.Column(
        mysql.TIMESTAMP,
        nullable=False,
        server_default=db.func.now()
    )

    character_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    character = db.relationship(
        'CharacterInfo',
        backref="leaderboards",
        passive_deletes=True
    )

    time = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

    score = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        server_default='0'
    )

class Mail(db.Model):
    __tablename__ = 'mail'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        mysql.BIGINT,
        nullable=False
    )

    sender_name = db.Column(
        mysql.VARCHAR(35),
        nullable=False
    )

    receiver_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    receiver = db.relationship(
        'CharacterInfo',
        backref="mail",
        passive_deletes=True
    )

    receiver_name = db.Column(
        mysql.VARCHAR(35),
        nullable=False
    )

    time_sent = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False
    )

    subject = db.Column(
        mysql.TEXT,
        nullable=False
    )

    body = db.Column(
        mysql.TEXT,
        nullable=False
    )

    attachment_id = db.Column(
        mysql.BIGINT,
        nullable=False,
        server_default='0'
    )

    attachment_lot = db.Column(
        mysql.INTEGER,
        nullable=False,
        server_default='0'
    )

    attachment_subkey = db.Column(
        mysql.BIGINT,
        nullable=False,
        server_default='0'
    )

    attachment_count = db.Column(
        mysql.INTEGER(),
        nullable=False,
        server_default='0'
    )

    was_read = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

class ObjectIDTracker(db.Model):
    __tablename__ = 'object_id_tracker'
    last_object_id = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
        primary_key=True,
        server_default='0'
    )

class PetNames(db.Model):
    __tablename__ = 'pet_names'
    id = db.Column(mysql.BIGINT, primary_key=True)
    per_name = db.Column(
        mysql.TEXT,
        nullable=False
    )
    approved = db.Column(
        mysql.INTEGER(unsigned=True),
        nullable=False,
        server_default='0'
    )

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(mysql.BIGINT, primary_key=True)
    owner_id  = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    owner = db.relationship(
        'CharacterInfo',
        foreign_keys=[owner_id],
        backref="properties_owner",
        passive_deletes=True
    )

    template_id = db.Column(
        mysql.INTEGER(unsigned=True),
        nullable=False,
        server_default='0'
    )

    clone_id  = db.Column(
        mysql.BIGINT(unsigned=True),
        db.ForeignKey(CharacterInfo.prop_clone_id, ondelete='CASCADE'),
        nullable=False
    )

    clone = db.relationship(
        'CharacterInfo',
        foreign_keys=[clone_id],
        backref="properties_clone",
        passive_deletes=True
    )

    name = db.Column(
        mysql.TEXT,
        nullable=False
    )

    description = db.Column(
        mysql.TEXT,
        nullable=False
    )

    rent_amount = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

    rent_due = db.Column(
        mysql.BIGINT,
        nullable=False,
    )

    privacy_option = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

    mod_approved = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    last_updated = db.Column(
        mysql.BIGINT,
        nullable=False,
    )

    time_claimed = db.Column(
        mysql.BIGINT,
        nullable=False,
    )

    rejection_reason = db.Column(
        mysql.TEXT,
        nullable=False
    )

    reputation = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
    )

    zone_id = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

class UGC(db.Model):
    __tablename__ = 'ugc'
    id = db.Column(mysql.BIGINT, primary_key=True)
    account_id = db.Column(
        db.Integer(),
        db.ForeignKey(Account.id, ondelete='CASCADE'),
        nullable=False
    )

    account = db.relationship(
        'Account',
        backref="ugc",
        passive_deletes=True
    )

    character_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    character = db.relationship(
        'CharacterInfo',
        backref="ugc",
        passive_deletes=True
    )

    is_optimized = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    lxfml = db.Column(
        mysql.MEDIUMBLOB(),
        nullable=False
    )

    bake_ao = db.Column(
        mysql.BOOLEAN,
        nullable=False,
        server_default='0'
    )

    filename = db.Column(
        mysql.TEXT,
        nullable=False,
        server_default=''
    )

class PropertyContent(db.Model):
    __tablename__ = 'properties_contents'
    id = db.Column(mysql.BIGINT, primary_key=True)
    property_id = db.Column(
        db.BIGINT,
        db.ForeignKey(Property.id, ondelete='CASCADE'),
        nullable=False
    )

    property_data = db.relationship(
        'Property',
        backref="properties_contents",
        passive_deletes=True
    )

    ugc_id = db.Column(
        db.BIGINT,
        db.ForeignKey(UGC.id, ondelete='CASCADE'),
        nullable=False
    )

    ugc = db.relationship(
        'UGC',
        backref="properties_contents",
        passive_deletes=True
    )

    lot = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

    x = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    y = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    z = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    rx = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    ry = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    rz = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

    rw = db.Column(
        mysql.FLOAT(),
        nullable=False,
    )

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(mysql.BIGINT, primary_key=True)

    character_id = db.Column(
        mysql.BIGINT,
        db.ForeignKey(CharacterInfo.id, ondelete='CASCADE'),
        nullable=False
    )

    character = db.relationship(
        'CharacterInfo',
        backref="avtivity_log",
        passive_deletes=True
    )

    activity = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

    time = db.Column(
        mysql.BIGINT(unsigned=True),
        nullable=False,
    )

    map_id = db.Column(
        mysql.INTEGER,
        nullable=False,
    )

class BugReports(db.Model):
    __tablename__ = 'bug_reports'
    id = db.Column(mysql.BIGINT, primary_key=True)

    body = db.Column(
        mysql.TEXT,
        nullable=False
    )

    client_version = db.Column(
        mysql.TEXT,
        nullable=False
    )

    other_player_id = db.Column(
        mysql.TEXT,
        nullable=False
    )

    selection = db.Column(
        mysql.TEXT,
        nullable=False
    )

    submitted = db.Column(
        mysql.TIMESTAMP,
        nullable=False,
        server_default=db.func.now()
    )

class servers(db.Model):
    __tablename__ = 'servers'
    id = db.Column(mysql.BIGINT, primary_key=True)
    name = db.Column(
        mysql.TEXT,
        nullable=False
    )

    ip = db.Column(
        mysql.TEXT,
        nullable=False
    )

    port = db.Column(
        mysql.INTEGER,
        nullable=False
    )

    state = db.Column(
        mysql.INTEGER,
        nullable=False
    )

    version = db.Column(
        mysql.INTEGER,
        nullable=False,
        server_default='0'
    )
