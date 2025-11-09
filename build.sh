#!/usr/bin/env bash
# Exit on error
set -o errexit
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate

# --- Force the password reset ---
python manage.py force_set_admin_password
