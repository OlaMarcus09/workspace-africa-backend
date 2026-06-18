import os
import sys

# Add current directory to path so Django can find 'core'
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# --- AUTOMATED DATABASE SCHEMA BUILDER (RUNS AT FUNCTION INIT) ---
try:
    import django
    django.setup()
    from django.core.management import call_command
    
    print("CRITICAL: Checking and applying structural migrations to fresh database...")
    # This automatically builds your tables on the new Neon instance safely
    call_command('migrate', interactive=False)
    print("SUCCESS: Database schema fully populated.")
except Exception as db_err:
    print(f"MIGRATION_ERROR: Structural migration skipped/failed -> {db_err}")

# --- GET WSGI HANDLER ---
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel expects 'app' variable
app = application
