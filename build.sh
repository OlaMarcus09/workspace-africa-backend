#!/bin/bash
echo "==> Starting Vercel Static Compilation Hook..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
echo "==> Static Assets successfully compiled into staticfiles/ directory."
