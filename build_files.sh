#!/bin/bash
echo "Installing Requirements..."
pip install -r requirements.txt

echo "Collecting Static Files to /staticfiles_build..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build Completed!"
