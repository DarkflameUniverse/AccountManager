#!/usr/bin/env bash

# unzip/copy brickdb from client to the right places
unzip /app/luclient/res/brickdb.zip -d /app/static/brickdb
cp -r /app/luclient/res/brickprimitives /app/static/brickdb

flask db upgrade
gunicorn -b :8000 -w 4 wsgi:app
