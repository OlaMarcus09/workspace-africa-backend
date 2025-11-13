#!/bin/bash
set -o errexit

echo "=== Starting Build Process ==="

# Install dependencies
echo "=== Installing dependencies ==="
pip install -r requirements.txt

# Run database migrations
echo "=== Running database migrations ==="
python manage.py migrate

# Create superuser if none exists
echo "=== Creating superuser if needed ==="
python manage.py createsuperuser_if_none

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Build completed successfully! ==="
