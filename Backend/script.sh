#!/bin/sh

python3 /Backend/code/manage.py makemigrations Backend
python3 /Backend/code/manage.py	makemigrations
python3 /Backend/code/manage.py	migrate --verbosity=3

python /Backend/code/manage.py createsuperuser --username=${DJANGO_SUPERUSER} --email=${DJANGO_SUPERUSER_EMAIL} --noinput

#gunicorn --bind 0.0.0.0:8000 --workers 3 Register.code.configs.wsgi:application
exec python3 /Backend/code/manage.py runserver 0.0.0.0:${BACKEND_PORT}