import os
import sys

# Add current directory to path so Django can find 'core'
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel expects 'app' variable
app = application
