from flask_marshmallow import Marshmallow
from app.models import *
ma = Marshmallow()

class PlayKeySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PlayKey
        include_relationships = False
        load_instance = True
        include_fk = True

class PropertySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Property
        include_relationships = False
        load_instance = True
        include_fk = False


class CharacterXMLSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CharacterXML
        include_relationships = False
        load_instance = True
        include_fk = False


class CharacterInfoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CharacterInfo
        include_relationships = False
        load_instance = True
        include_fk = False

    charxml = ma.Nested(CharacterXMLSchema)
    properties = ma.Nested(PropertySchema, many=True)


class AccountSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Account
        include_relationships = False
        load_instance = True
        include_fk = False

    play_key = ma.Nested(PlayKeySchema)
    charinfo = ma.Nested(CharacterInfoSchema, many=True)


class AccountInvitationSchema(ma.SQLAlchemyAutoSchema): #  noqa
    class Meta:
        model = AccountInvitation
        include_relationships = True
        load_instance = True
        include_fk = True

    invite_by_user = ma.Nested(AccountSchema)

