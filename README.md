# Darkflame Universe Account Manager v2

Logo Here
# Deployment

Need an LU client

drop in app/luclient or bind mount docker `/path/to/client:/app/luclient

Needs to have sqlite conversion of cdclient.fdb
Needs to be located app/luclient/res/cdclient.sqlite

## Docker

TODO: Write instructions

### Environmental Variables
 * Required:
    * APP_SECRET_KEY (Must be provided)
    * APP_DATABASE_URI (Must be provided)
 * Optional
    * USER_ENABLE_REGISTER (Default: True)
    * USER_ENABLE_EMAIL (Default: True, Needs Mail to be configured)
    * USER_ENABLE_CONFIRM_EMAIL (Default: True)
    * USER_ENABLE_INVITE_USER (Default: False)
    * USER_REQUIRE_INVITATION (Default: False)
    * REQUIRE_PLAY_KEY (Default: True)
    * MAIL_SERVER (Default: smtp.gmail.com)
    * MAIL_PORT (Default: 587)
    * MAIL_USE_SSL (Default: False)
    * MAIL_USE_TLS (Default: True)
    * MAIL_USERNAME (Default: None)
    * MAIL_PASSWORD (Default: None)
    * USER_EMAIL_SENDER_NAME (Default: None)
    * USER_EMAIL_SENDER_EMAIL (Default: None)


## Manual

TODO: Write this, even though people should use docker

# Development

Please use [Editor Config](https://editorconfig.org/)

 * `flask run` to run local dev server
