import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from spaces.models import PartnerSpace

User = get_user_model()

def onboard_partners():
    partners = [
        {"name": "Sebs Hub", "email": "sebs@workspace.africa", "username": "Sebs_Hub"},
        {"name": "Worknub", "email": "worknub@workspace.africa", "username": "Worknub"},
        {"name": "Stargate", "email": "stargate@workspace.africa", "username": "Stargate"},
        {"name": "TheBunker", "email": "thebunker@workspace.africa", "username": "TheBunker"},
        {"name": "Nesta Coworking", "email": "nesta@workspace.africa", "username": "Nesta_Coworking"},
        {"name": "CyberHaven", "email": "cyberhaven@workspace.africa", "username": "CyberHaven"},
        {"name": "Atelier Cafe", "email": "atelier@workspace.africa", "username": "Atelier_Cafe"},
    ]
    
    default_password = 'WorkSpace2026!'
    
    print("🚀 Starting Ibadan Bulk Onboarding...")
    
    for p in partners:
        # 1. Create or Update the User as a PARTNER
        user, created = User.objects.get_or_create(
            email=p["email"],
            defaults={
                'username': p["username"],
                'user_type': 'PARTNER',
                'is_active': True
            }
        )
        
        if created:
            user.set_password(default_password)
            user.save()
            print(f"👤 Created User: {p['email']} (PARTNER)")
        else:
            # Force the PARTNER role update if they already exist
            user.user_type = 'PARTNER'
            user.set_password(default_password)
            user.save()
            print(f"🔄 Updated User: {p['email']} to PARTNER")

        # 2. Create the Physical Space (Removed the unknown 'location' field)
        space, space_created = PartnerSpace.objects.get_or_create(
            owner=user,
            defaults={
                'name': p["name"],
            }
        )
        
        if space_created:
            print(f"🏢 Created Space: {p['name']} linked to {p['email']}")
        else:
            print(f"✅ Space already exists for: {p['name']}")

    print("\n🎉 All 7 Ibadan nodes successfully onboarded!")

if __name__ == "__main__":
    onboard_partners()