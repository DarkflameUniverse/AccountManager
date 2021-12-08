from flask_wtf import FlaskForm

from flask_user.forms import (
    unique_email_validator,
    password_validator,
    unique_username_validator
)
from flask_user import UserManager
from wtforms import (
    StringField,
    HiddenField,
    PasswordField,
    BooleanField,
    SubmitField,
    validators,
    IntegerField
)

from wtforms.validators import DataRequired

from app.models import PlayKey

def validate_play_key(form, field):
    """Validates a field for a valid phone number
    Args:
        form: REQUIRED, the field's parent form
        field: REQUIRED, the field with data
    Returns:
        None, raises ValidationError if failed
    """
    field.data = PlayKey.key_is_valid(key_string=field.data)
    return


class CustomUserManager(UserManager):
    def customize(self, app):
        self.RegisterFormClass = CustomRegisterForm


class CustomRegisterForm(FlaskForm):
    """Registration form"""
    next = HiddenField()
    reg_next = HiddenField()

    # Login Info
    email = StringField(
        'E-Mail',
        validators=[
            DataRequired(),
            validators.Email('Invalid email address'),
            unique_email_validator,
        ]
    )

    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            unique_username_validator,
        ]
    )

    play_key_id = StringField(
        'Play Key',
        validators=[
            DataRequired(),
            validate_play_key,
        ]
    )

    password = PasswordField('Password', validators=[
        DataRequired(),
        password_validator
    ])
    retype_password = PasswordField('Retype Password', validators=[
        validators.EqualTo('password', message='Passwords did not match')
    ])

    invite_token = HiddenField('Token')

    submit = SubmitField('Register')

class CreatePlayKeyForm(FlaskForm):

    count = IntegerField(
        'How many Play Keys to create',
        validators=[DataRequired()]
    )
    uses = IntegerField(
        'How many uses each new play key will have',
        validators=[DataRequired()]
    )
    submit = SubmitField('Create!')

class EditPlayKeyForm(FlaskForm):

    active = BooleanField(
        'Active'
    )

    uses = IntegerField(
        'Play Key Uses'
    )

    submit = SubmitField('Submit')
