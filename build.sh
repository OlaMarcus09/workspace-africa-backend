#!/bin/bash

# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect static files without asking for yes/no confirmation
python manage.py collectstatic --noinput