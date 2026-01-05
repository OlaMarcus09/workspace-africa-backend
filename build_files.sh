#!/bin/bash

# Install all dependencies
echo "Installing Requirements..."
pip install -r requirements.txt

# Create the static files (CSS/JS)
echo "Collecting Static Files..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build Process Completed!"
