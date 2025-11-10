#!/bin/bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create any missing migrations first
python manage.py makemigrations --noinput

# Then apply all migrations
python manage.py migrate --noinput

# Create superuser if none exists
python manage.py createsuperuser_if_none

# Collect static files
python manage.py collectstatic --noinput

echo "Build completed successfully!"
