import os
import sys

# Add current directory to path so Django can find the root modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize the WSGI application
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
