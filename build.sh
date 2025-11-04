#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# --- NEW: Create Superuser (non-interactively) ---
# This Python script runs *inside* the shell command.
# It checks if the user exists first, so it's safe to run on every deploy.
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')

if email and password and username:
    if not User.objects.filter(email=email).exists():
        print('Creating superuser...')
        User.objects.create_superuser(
            email=email,
            username=username,
            password=password
        )
        print('Superuser created.')
    else:
        print('Superuser already exists.')
else:
    print('Superuser env vars not set, skipping creation.')
