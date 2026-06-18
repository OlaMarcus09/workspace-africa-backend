import os
import sys

# Add current directory to path so Django can find 'core'
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# --- AUTOMATED DATABASE SEEDER & ACCOUNT UPGRADER ---
try:
    import django
    django.setup()
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    
    # 1. Run migrations to ensure structural tables exist
    print("CRITICAL: Aligning database topology...")
    call_command('migrate', interactive=False)
    
    # 2. Grant superuser permissions to your live account
    User = get_user_model()
    target_email = 'olawalemarcus92@gmail.com'
    admin_user = User.objects.filter(email=target_email).first()
    
    if admin_user:
        if not admin_user.is_superuser or not admin_user.is_staff:
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            print(f"SUCCESS: Upgraded {target_email} to system administrator.")
    else:
        print(f"NOTICE: Account {target_email} not found yet. Seeder will retry on next reload.")

    # 3. Dynamic Plan Initialization (Breaks the Frontend Loading Loop)
    # Check if your specific app model for subscriptions/plans has a custom model name
    # We will try a safe database creation pattern to inject fallback data entries
    try:
        from django.apps import apps
        # Look for a Model representing pricing tiers (commonly 'Plan' inside a 'spaces' or 'users' app)
        if apps.has_model('spaces', 'Plan'):
            Plan = apps.get_model('spaces', 'Plan')
            if Plan.objects.count() == 0:
                Plan.objects.create(name="16 Days Access", price=45000, access_tier="STANDARD")
                Plan.objects.create(name="Flex Unlimited", price=90000, access_tier="PREMIUM")
                print("SUCCESS: Default service tiers seeded into Neon.")
    except Exception as model_err:
        print(f"SEEDER_WARNING: App model seeding skipped -> {model_err}")

except Exception as db_err:
    print(f"BOOT_ERROR: Verification sequence bypassed -> {db_err}")

# --- GET WSGI HANDLER ---
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel expects 'app' variable
app = application
