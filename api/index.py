import os
import sys
import traceback

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    # Attempt to boot up the Django application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    app = application

except Exception as e:
    # If the boot sequence crashes (Syntax Error, Import Error, etc.), 
    # catch the traceback and render it as a plain text web response.
    error_traceback = traceback.format_exc()
    print(f"CRITICAL BOOT FAILURE: {error_traceback}")
    
    def fallback_application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [error_traceback.encode('utf-8')]
    
    app = fallback_application
