#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies from our clean file
pip install -r requirements.txt

# Collect static files (for the admin panel)
python manage.py collectstatic --no-input

# Apply any new database migrations
python manage.py migrate
