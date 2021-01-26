#!/bin/sh

# migrate database
python manage.py migrate

exec "$@"
