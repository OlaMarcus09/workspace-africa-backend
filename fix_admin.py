import os
import sys
import django

# 1. Setup Django
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def fix_admin():
    print("--- 🔐 ADMIN ACCOUNT FIXER ---")
    
    # YOUR SPECIFIC DETAILS
    target_email = "olawalemarcus92@gmail.com"
    target_username = "WorkSpaceAfrica"
    target_password = "admin123"

    try:
        # 1. Try to find the user by email
        user = User.objects.get(email=target_email)
        print(f"\n✅ ACCOUNT FOUND: {target_email}")
        
        # 2. Force update the username and password
        user.username = target_username
        user.set_password(target_password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print(f"✅ UPDATED USERNAME TO: {target_username}")
        print(f"✅ PASSWORD RESET TO: {target_password}")

    except User.DoesNotExist:
        print(f"\n❌ Account not found. Creating new Superuser...")
        
        # 3. Create if it doesn't exist
        User.objects.create_superuser(
            username=target_username, 
            email=target_email, 
            password=target_password
        )
        print(f"✅ NEW SUPERUSER CREATED!")

    print("--------------------------------")
    print(f"👉 GO LOGIN NOW WITH:")
    print(f"Username: {target_username}")
    print(f"Password: {target_password}")

if __name__ == "__main__":
    fix_admin()
