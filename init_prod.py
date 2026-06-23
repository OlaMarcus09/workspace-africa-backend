import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def fix_admin():
    email = 'workspaceafrica.hq@gmail.com'
    password = 'WorkSpace2026!'
    
    try:
        # If user exists, FORCE the password reset and admin rights
        user = User.objects.get(email=email)
        user.set_password(password) # This generates the perfect hash!
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.user_type = 'ADMIN'
        user.save()
        print(f"✅ SUCCESS: {email} password and admin rights have been forcefully reset.")
        
    except User.DoesNotExist:
        # If user doesn't exist, create them
        User.objects.create_superuser(
            email=email,
            username='hq_admin',
            password=password,
            user_type='ADMIN'
        )
        print(f"✅ SUCCESS: {email} Admin Created.")

if __name__ == "__main__":
    fix_admin()
    