import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from spaces.models import PartnerSpace

print("🧹 Starting Cleanup...")

# 1. Delete the Auto-Generated Spaces (Created by the Signal)
# These are named like "admin_sebs's Space"
generic_spaces = PartnerSpace.objects.filter(name__contains="'s Space")
if generic_spaces.exists():
    print(f"Found {generic_spaces.count()} generic spaces (e.g., admin_sebs's Space).")
    generic_spaces.delete()
    print("❌ Deleted generic spaces.")
else:
    print("✨ No generic spaces found.")

# 2. Delete Orphaned Spaces (Spaces with NO owner)
# Since we just ran the linking script, valid spaces MUST have an owner.
# Any space without an owner now is a leftover duplicate.
orphans = PartnerSpace.objects.filter(owner__isnull=True)
if orphans.exists():
    print(f"Found {orphans.count()} orphaned spaces (No owner).")
    for space in orphans:
        print(f"   - Deleting: {space.name}")
    orphans.delete()
    print("❌ Deleted orphaned spaces.")
else:
    print("✨ No orphaned spaces found.")

# 3. List the Final, Valid Spaces
print("\n✅ FINAL ACTIVE NETWORK NODES:")
valid_spaces = PartnerSpace.objects.all().select_related('owner')
for space in valid_spaces:
    owner_name = space.owner.username if space.owner else "NO OWNER (Error)"
    print(f"📍 {space.name} (Owner: {owner_name})")
