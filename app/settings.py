# Settings common to all environments (development|staging|production)

# Application settings
APP_NAME = "DLU Account Management and Dashboard"
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

# Flask settings
CSRF_ENABLED = True

# Flask-SQLAlchemy settings
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_TIME_LIMIT = 86400

# Flask-User settings
USER_APP_NAME = APP_NAME
USER_ENABLE_CHANGE_PASSWORD = True  # Allow users to change their password
USER_ENABLE_CHANGE_USERNAME = False  # Allow users to change their username
USER_ENABLE_CONFIRM_EMAIL = True  # Force users to confirm their email
USER_ENABLE_FORGOT_PASSWORD = True  # Allow users to reset their passwords
USER_ENABLE_EMAIL = True  # Register with Email
USER_ENABLE_REGISTRATION = True  # Allow new users to register
USER_ENABLE_INVITE_USER = True  # Allow users to be invited
USER_REQUIRE_INVITATION = False  # Only invited users may register
USER_REQUIRE_RETYPE_PASSWORD = True  # Prompt for `retype password` in:
USER_ENABLE_USERNAME = False  # Register and Login with username

# Password hashing settings
USER_PASSLIB_CRYPTCONTEXT_SCHEMES = ['bcrypt']  # bcrypt for password hashing

# Flask-User routing settings
USER_AFTER_LOGIN_ENDPOINT = "main.index"
USER_AFTER_LOGOUT_ENDPOINT = "main.index"
USER_AFTER_EDIT_USER_PROFILE_ENDPOINT = 'user.profile'
