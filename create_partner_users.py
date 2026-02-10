import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from spaces.models import PartnerSpace

User = get_user_model()

# The 7 Nodes
PARTNERS = [
    {'username': 'admin_sebs', 'email': 'sebs@workspace.africa', 'space_name': "Seb's Hub"},
    {'username': 'admin_worknub', 'email': 'worknub@workspace.africa', 'space_name': "Worknub"},
    {'username': 'admin_stargate', 'email': 'stargate@workspace.africa', 'space_name': "Stargate Workstation"},
    {'username': 'admin_bunker', 'email': 'bunker@workspace.africa', 'space_name': "The Bunker"},
    {'username': 'admin_nesta', 'email': 'nesta@workspace.africa', 'space_name': "Nesta Co-work"},
    {'username': 'admin_cyberhaven', 'email': 'cyberhaven@workspace.africa', 'space_name': "Cyberhaven"},
    {'username': 'admin_atelier', 'email': 'atelier@workspace.africa', 'space_name': "Atelier Café"},
]

print("🌱 Creating Partner Humans...")

for partner in PARTNERS:
    # 1. Create or Get the User
    user, created = User.objects.get_or_create(
        username=partner['username'],
        email=partner['email'],
        defaults={'user_type': 'PARTNER'}
    )
    
    if created:
        user.set_password('password123') # Default password
        user.save()
        print(f"👤 Created User: {partner['username']}")
    else:
        print(f"ℹ️  User exists: {partner['username']}")

    # 2. Link to Space
    try:
        space = PartnerSpace.objects.get(name=partner['space_name'])
        space.owner = user
        space.save()
        print(f"🔗 Linked {partner['username']} -> {partner['space_name']}")
    except PartnerSpace.DoesNotExist:
        print(f"⚠️  Space not found: {partner['space_name']} (Check spelling)")

print("✅ Partners Created and Linked!")
