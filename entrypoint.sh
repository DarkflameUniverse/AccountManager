#!/usr/bin/env bash

# unzip brickdb from client to the right places
unzip /app/luclient/res/brickdb.zip -d app/luclient/res/

flask db upgrade
gunicorn -b :8000 -w 4 wsgi:app
