#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser if none exists (your custom command)
python manage.py createsuperuser_if_none

# Collect static files
python manage.py collectstatic --noinput
