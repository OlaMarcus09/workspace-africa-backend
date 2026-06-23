import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # or your project name
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Fix HQ Account
hq = User.objects.get(email='workspaceafrica.hq@gmail.com')
hq.set_password('WorkSpace2026!') # Django handles the hashing correctly here
hq.is_superuser = True
hq.is_staff = True
hq.user_type = 'ADMIN'
hq.save()

print("HQ_ADMIN_RESTORED_SUCCESSFULLY")