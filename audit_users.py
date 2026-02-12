import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("🧹 STARTING USER AUDIT...")

# Delete users who are NOT partners and NOT superusers
users_to_delete = User.objects.filter(is_superuser=False, is_staff=False).exclude(user_type='PARTNER')

count = users_to_delete.count()
print(f"⚠️  Found {count} nomadic users to delete.")

if count > 0:
    users_to_delete.delete()
    print("✅ Deletion Complete.")
else:
    print("✨ No users to delete.")

# Verify Partners
print("\n🛡️  VERIFYING PARTNER ACCOUNTS:")
partners = User.objects.filter(user_type='PARTNER')
for p in partners:
    print(f"   👤 {p.username} | {p.email}")

print("\n✅ AUDIT COMPLETE.")
