# Darkflame Universe Account Manager v2

Logo
# Deployment

Environmental Variables:

 * Required:
    * APP_SECRET_KEY
    * APP_DATABASE_URI
 * Optional
    * USER_ENABLE_REGISTRATION (Default: True)
    * USER_ENABLE_EMAIL (Default: True, Needs Mail to be configured)
    * REQUIRE_PLAY_KEY (Default: True)
    * MAIL_SERVER (Default: smtp.gmail.com)
    * MAIL_PORT (Default: 587)
    * MAIL_USE_SSL (Default: False)
    * MAIL_USE_TLS (Default: True)
    * MAIL_USERNAME (Default: None)
    * MAIL_PASSWORD (Default: None)
    * USER_EMAIL_SENDER_NAME (Default: None)
    * USER_EMAIL_SENDER_EMAIL (Default: None)

## Docker

TODO: Write instructions


# Database

The database that is used is based on the DLU v1 Databases,
but completely defined in this app for easier interface via the
Object Relational Mapper (ORM) SqlAlchemy.

## Migration from DLU v1 Database

TODO: Implement, Maybe

## From Scratch

 * Make sure you have your venv setup and your db uri
 * Run `flask upgrade`

# Development

Please use [Editor Config](https://editorconfig.org/)

 * `flask run` to run local dev server
