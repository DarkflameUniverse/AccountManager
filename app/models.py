from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import UserMixin

import logging
from flask_sqlalchemy import BaseQuery
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

class Account(db.Model, UserMixin):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(35),
        nullable=False,
        unique=True
    )
    password = db.Column(
        db.String(),
        nullable=False,
        server_default=''
    )
    gm_level = db.Column(
        db.Integer(),
        nullable=False,
        server_default=0
    )
    locked
    banned
    play_key_id #fk
    created_at = db.Column(db.DateTime())
    mute_expire


    @staticmethod
    def get_user_by_id(*, user_id=None):
        return User.query.filter(user_id == User.id).first()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class CharacterInfo(db.Model):
    __tablename__ = 'charinfo'
    id = db.Column(db.Integer, primary_key=True)
    account_id #fk
    name
    pending_name
    needs_rename
    prop_clone_id
    last_login
    permission_map

class CharacterXML(db.Model):
    __tablename__ = 'charxml'
    id = db.Column(db.Integer, primary_key=True)
    xml_data

class command_log(db.model):
    __tablename__ = 'command_log'
    id = db.Column(db.Integer, primary_key=True)
    character_id
    command

class friends(db.model):
    __tablename__ = 'friends'
    player_id #fk
    friend_id #fk
    best_friend
    # primary compisote key of charinfo(id) fk's

class leaderboard(db.model):
    __tablename__ = 'leaderboard'
    id = db.Column(db.Integer, primary_key=True)
    game_id
    last_played
    character_id #fk
    time
    score

class mail(db.model):
    __tablename__ = 'mail'
    id = db.Column(db.Integer, primary_key=True)
    sender_id
    sender_name
    receiver_id #fk
    receiver_name
    time_sent
    subject
    body
    attachment_id
    attachment_lot
    attachment_subkey
    attachment_count
    was_read

class object_id_tracker(db.model):
    __tablename__ = 'object_id_tracker'
    last_object_id

class pet_names(db.model):
    __tablename__ = 'pet_names'
    id = db.Column(db.Integer, primary_key=True)
    per_name
    approved

class play_keys(db.model):
    __tablename__ = 'play_keys'
    id = db.Column(db.Integer, primary_key=True)
    key_string
    key_uses
    created_at
    active

class properties(db.model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    owner_id #fk
    template_id
    clone_id #fk charinfo(prop_clone_id)
    name
    description
    rent_amount
    rent_due
    privacy_option
    mod_approved
    last_updated
    time_claimed
    rejection_reason
    reputation
    zone_id

class ugc(db.model):
    __tablename__ = 'ugc'
    id = db.Column(db.Integer, primary_key=True)
    account_id #fk account
    character_id #fk charinfo
    is_optimized
    lxfml
    bake_ao
    filename

class properties_contents(db.model):
    __tablename__ = 'properties_contents'
    id = db.Column(db.Integer, primary_key=True)
    property_id #fk properties
    ugc_id
    lot
    x
    y
    z
    rx
    ry
    rz
    rw

class activity_log(db.model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    character_id #fk
    activity
    time
    map_id

class bug_reports(db.model):
    __tablename__ = 'bug_reports'
    id = db.Column(db.Integer, primary_key=True)
    body
    client_version
    other_player_id
    selection
    submitted

class servers(db.model):
    __tablename__ = 'servers'
    id = db.Column(db.Integer, primary_key=True)
    name
    ip
    port
    state
    version
