#!/usr/bin/env bash
# Exit on error
set -o errexit

# --- NEW FIX ---
# Force upgrade pip, setuptools, and wheel before anything else
pip install --upgrade pip setuptools wheel

# Now, install our dependencies
pip install -r requirements.txt

# Collect static files (for the admin panel)
python manage.py collectstatic --no-input

# Apply any new database migrations
python manage.py migrate
