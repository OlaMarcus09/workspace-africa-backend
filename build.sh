#!/bin/bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser_if_none
python manage.py collectstatic --noinput
echo "Build completed!"
