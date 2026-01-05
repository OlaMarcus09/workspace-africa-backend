import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

# --- RUNTIME FIX: Generate CSS on Boot ---
try:
    print("Collecting static files to /tmp/static...")
    call_command('collectstatic', interactive=False, clear=True, verbosity=0)
    print("Static files collected successfully.")
except Exception as e:
    print(f"Error collecting static files: {e}")

app = application
