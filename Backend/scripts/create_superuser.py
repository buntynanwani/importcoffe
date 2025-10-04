#!/usr/bin/env python3
"""Create or update a Django superuser when run inside the container.

Usage (inside container):
  python /Backend/scripts/create_superuser.py

Environment variables used (optional):
  DJANGO_SUPERUSER - username (default: admin)
  DJANGO_SUPERUSER_EMAIL - email (default: admin@example.com)
  DJANGO_SUPERUSER_PASSWORD - password (default: adminpassword)
"""
import os
import sys

# Ensure project path is on sys.path and DJANGO_SETTINGS_MODULE is set
sys.path.insert(0, '/Backend/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configs.settings')

import django
django.setup()

from django.contrib.auth import get_user_model


def main():
    User = get_user_model()

    # Treat empty strings as not provided (os.environ.get may return "")
    # Support either DJANGO_SUPERUSER (legacy) or DJANGO_SUPERUSER_USERNAME (explicit)
    username = os.environ.get('DJANGO_SUPERUSER') or os.environ.get('DJANGO_SUPERUSER_USERNAME') or 'admin'
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL') or 'admin@example.com'
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD') or 'adminpassword'

    # Debug: show what we resolved from environment
    print('DEBUG: resolved username={!r} email={!r} password_set={}'.format(username, email, bool(password)))

    # Support custom user models that may use a different USERNAME_FIELD
    username_field = getattr(User, 'USERNAME_FIELD', 'username')
    lookup = {username_field: username}

    # Build kwargs for create_superuser: place username into the proper field
    create_kwargs = {username_field: username}
    # Pass email explicitly if the model still has an 'email' field
    if username_field != 'email':
        create_kwargs['email'] = email

    if not User.objects.filter(**lookup).exists():
        User.objects.create_superuser(**create_kwargs, password=password)
        print('Created superuser ({}={})'.format(username_field, username))
    else:
        user = User.objects.get(**lookup)
        # Update email if present
        if hasattr(user, 'email'):
            user.email = email
        # Update password
        user.set_password(password)
        user.save()
        print('Updated superuser ({}={})'.format(username_field, username))


if __name__ == '__main__':
    main()
