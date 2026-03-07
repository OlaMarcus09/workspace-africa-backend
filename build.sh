#!/bin/bash

# 1. Create and activate a temporary virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies securely inside the virtual environment
pip install -r requirements.txt

# 3. Collect static files for the CDN
python manage.py collectstatic --noinput