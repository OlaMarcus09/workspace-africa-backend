import os
import sys
import django

# 1. Fix Python Path to find 'core'
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)

# 2. Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from spaces.models import PartnerSpace, Plan

def seed():
    print("🌱 Starting Database Seed...")

    # ==========================================
    # 1. SEED PARTNER SPACES (7 Real Partners)
    # ==========================================
    print("... Creating Partner Spaces")
    
    partners = [
        {"name": "Seb's Hub", "address": "32 Awolowo Ave, Bodija, Ibadan", "tier": "STANDARD", "rate": 2500},
        {"name": "Worknub", "address": "West One, Agodi GRA, Ibadan", "tier": "PREMIUM", "rate": 3500},
        {"name": "Stargate Workstation", "address": "Cocoa House, Dugbe, Ibadan", "tier": "PREMIUM", "rate": 4500},
        {"name": "The Bunker", "address": "Ring Road, Ibadan", "tier": "PREMIUM", "rate": 15000},
        {"name": "Nesta Co-work", "address": "Bashorun Estate, Akobo, Ibadan", "tier": "STANDARD", "rate": 4000},
        {"name": "Cyberhaven", "address": "Okunmade St, Mokola, Ibadan", "tier": "STANDARD", "rate": 2500},
        {"name": "Atelier Café", "address": "Jericho, Ibadan", "tier": "PREMIUM", "rate": 3500},
    ]

    for p in partners:
        # Using update_or_create to prevent duplicates
        space, created = PartnerSpace.objects.update_or_create(
            name=p["name"],
            defaults={
                "address": p["address"],
                "access_tier": p["tier"],
                "payout_per_checkin_ngn": p["rate"],
                "amenities": "WiFi, Power, AC, Coffee"
            }
        )
        if created:
            print(f"📍 Created Space: {p['name']}")
        else:
            print(f"🔄 Updated Space: {p['name']}")

    # ==========================================
    # 2. SEED SUBSCRIPTION PLANS (New Pricing)
    # ==========================================
    print("\n... Creating Subscription Plans")

    plans = [
        {
            "name": "FLEX_BASIC",
            "price": 27000.00,
            "days": 8,
            "tier": "STANDARD"
        },
        {
            "name": "FLEX_PRO",
            "price": 55000.00,
            "days": 16,
            "tier": "PREMIUM"
        },
        {
            "name": "FLEX_UNLIMITED",
            "price": 75000.00,
            "days": 999, # Internal code for unlimited
            "tier": "PREMIUM"
        }
    ]

    for plan_data in plans:
        plan, created = Plan.objects.update_or_create(
            name=plan_data["name"],
            defaults={
                "price_ngn": plan_data["price"],
                "included_days": plan_data["days"],
                "access_tier": plan_data["tier"]
            }
        )
        if created:
            print(f"💳 Created Plan: {plan_data['name']} @ N{plan_data['price']}")
        else:
            print(f"🔄 Updated Plan: {plan_data['name']}")

    print("\n🚀 SEED COMPLETE! Database is populated.")

if __name__ == "__main__":
    seed()
