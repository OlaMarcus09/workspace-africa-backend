#!/bin/bash
echo "==> Starting Vercel Static Compilation Hook..."

# FIXED: Bypass Vercel's new strict uv-managed environment block
python3 -m pip install -r requirements.txt --break-system-packages

# Compile the styles so WhiteNoise can serve them
python3 manage.py collectstatic --noinput --clear

echo "==> Static Assets successfully compiled into staticfiles/ directory."
