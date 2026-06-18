import os
import sys
import traceback

# 1. FORCE TOP-LEVEL DEFINITIONS FOR VERCEL STATIC PARSER
app = None
application = None

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    # 2. ATTEMPT TO INITIALIZE DJANGO
    from django.core.wsgi import get_wsgi_application
    django_app = get_wsgi_application()
    
    # Map back to global handlers
    app = django_app
    application = django_app

except Exception as e:
    # 3. CRASH CAPTURE FALLBACK
    error_traceback = traceback.format_exc()
    print(f"CRITICAL BOOT FAILURE:\n{error_traceback}")
    
    def fallback_handler(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, headers)
        return [error_traceback.encode('utf-8')]
    
    app = fallback_handler
    application = fallback_handler
