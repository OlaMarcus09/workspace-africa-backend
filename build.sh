#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Upgrade pip
pip install --upgrade pip

# 2. Install dependencies (with the new pip)
pip install -r requirements.txt

# 3. Collect static files
python manage.py collectstatic --no-input

# 4. Apply database migrations
python manage.py migrate
