import click
import json
from flask.cli import with_appcontext
import random, string, datetime
from flask_user import current_app
from app import db
from app.models import Account, PlayKey, Zone

@click.command("init_db")
@click.argument('drop_tables', nargs=1)
@with_appcontext
def init_db(drop_tables=False):
    """ Initialize the database."""

    print('Initializing Database.')
    if drop_tables:
        print('Dropping all tables.')
        db.drop_all()
    print('Creating all tables.')
    db.create_all()
    print('Database has been initialized.')
    return


@click.command("init_accounts")
@with_appcontext
def init_accounts():
    """ Initialize the accounts."""

    # Add accounts
    print('Creating Admin account.')
    admin_account = find_or_create_account(
        'admin',
        'example@example.com',
        'Nope',
    )


    return


def find_or_create_account(name, email, password, gm_level=9):
    """ Find existing account or create new account """
    account = Account.query.filter(Account.email == email).first()
    if not account:
        key = ""
        for j in range(4):
            key += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-'
        # Remove last dash
        key = key[:-1]

        play_key = PlayKey(
            key_string=key
        )
        db.session.add(play_key)
        db.session.commit()

        play_key = PlayKey.query.filter(PlayKey.key_string == key).first()
        account = Account(email=email,
                    username=name,
                    password=current_app.user_manager.password_manager.hash_password(password),
                    play_key_id=play_key.id,
                    email_confirmed_at=datetime.datetime.utcnow(),
                    gm_level=gm_level
                )
        play_key.key_uses = 0
        db.session.add(account)
        db.session.add(play_key)
        db.session.commit()
    return # account


@click.command("init_data")
@with_appcontext
def init_data():
    zones = {
        "1000": "Venture Explorer",
        "1001": "Return to the Venture Explorer",
        "1100": "Avant Gardens",
        "1101": "Avant Gardens Survival",
        "1102": "Spider Queen Battle",
        "1150": "Block Yard",
        "1151": "Avant Grove",
        "1200": "Nimbus Station",
        "1201": "Pet Cove",
        "1203": "Vertigo Loop Racetrack",
        "1204": "The Battle of Nimbus Station",
        "1250": "Nimbus Rock",
        "1251": "Nimbus Isle",
        "1300": "Gnarled Forest",
        "1302": "Cannon Cove Shooting Gallery",
        "1303": "Keelhaul Canyon Racetrack",
        "1350": "Chantey Shanty",
        "1400": "Forbidden Valley",
        "1402": "Forbidden Valley Dragon Battle",
        "1403": "Dragonmaw Chasm Racetrack",
        "1450": "Raven Bluff",
        "1500": "LUP Station",
        "1600": "Starbase 3001",
        "1601": "DeepFreeze",
        "1602": "Robot City",
        "1603": "MoonBase",
        "1604": "Portabello",
        "1700": "LEGO Club",
        "1800": "Crux Prime",
        "1900": "Nexus Tower",
        "2000": "Ninjago Monastery",
        "20000": "MBL Station",
        "2001": "Battle Against Frakjaw!",
        "20022": "Moonbase",
        "20061": "Port-a-bello",
        "20101": "Deep Freeze",
        "20147": "Robot City",
    }

    for zone_id in zones:
        new_zone = Zone(id=zone_id, name=zones[zone_id])
        db.session.add(new_zone)
    db.session.commit()
