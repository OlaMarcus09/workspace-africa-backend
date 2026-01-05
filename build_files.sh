#!/bin/bash
echo "Installing Requirements..."
pip install -r requirements.txt

echo "Collecting Static Files..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build Completed!"
