import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv  # Add this line

# Load environment variables from .env file
load_dotenv()  # Add this line

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Paystack Keys ---
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1').split(',')

# --- Frontend URLs (from Render Env) ---
PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL', 'http://localhost:3000/payment-success')
PAYMENT_CALLBACK_URL = os.environ.get('PAYMENT_CALLBACK_URL', 'http://localhost:8000/api/payments/verify/')

# Rest of your settings...
