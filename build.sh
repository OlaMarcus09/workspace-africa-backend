#!/bin/bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Apply all migrations (this will add the missing field on Render)
python manage.py migrate --noinput

# Create superuser if none exists
python manage.py createsuperuser_if_none

# Collect static files
python manage.py collectstatic --noinput

echo "Build completed successfully!"
