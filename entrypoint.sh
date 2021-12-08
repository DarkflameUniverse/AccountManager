#!/usr/bin/env bash

flask db upgrade
gunicorn -b :8000 -w 4 wsgi:app
