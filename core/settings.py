import os
from pathlib import Path
import dj_database_url
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# Current file is core/settings.py, so parent.parent is root
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings (Enforced via safe environment extractions)
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    # Fail safely locally if developers haven't established an active shell scope
    SECRET_KEY = 'django-insecure-development-fallback-key-do-not-use-in-production'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# FIXED: Allow all Vercel dynamic subdomains to avoid connection rejections during live validation
if DEBUG:
    ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']
else:
    ALLOWED_HOSTS = ['.vercel.app', 'workspace-africa-backend.vercel.app']

CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://workspace-africa-backend.vercel.app'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt', 
    'corsheaders',
    
    # Custom apps
    'users',
    'spaces',
    'teams',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Serves Django Admin CSS styles on Vercel
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Must remain above CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Extract the environment variable cleanly
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

# If it's an empty string or completely missing, fallback gracefully for the Vercel build container step
if not DATABASE_URL:
    if not DEBUG:
        print("WARNING: DATABASE_URL is empty. Falling back to local scheme for build execution context.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=0,  # CRITICAL FIX: Changed from 600 to 0 to stop dead serverless pooling crashes on Vercel
            ssl_require=not DEBUG
        )
    }

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES CONFIGURATION (VERCEL SERVERLESS STORAGE) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# CRITICAL FIX: Downgraded to standard StaticFilesStorage to completely stop the 500 Manifest crashes on API routes
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'

# --- AUTHENTICATION & JWT CONFIGURATION ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Strict CORS filtering config to protect database tables from external browser origins
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://workspace-africa-gateway.vercel.app',
    'https://workspace-nomad.vercel.app',
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$", # Authorizes Vercel preview testing links seamlessly
]
CORS_ALLOW_CREDENTIALS = True

# Defend against endpoint mismatches where URLs lack a trailing slash
APPEND_SLASH = True

# --- PAYMENT INTEGRATION ---
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY')

if not PAYSTACK_SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("PAYSTACK_SECRET_KEY environment variable is required in production.")
