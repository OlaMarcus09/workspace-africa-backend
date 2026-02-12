import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from spaces.models import Plan

# These MUST match what is in your frontend pages/plans.js
UPDATES = {
    'FLEX_BASIC': 'PLN_qhytgtizn15iepe',
    'FLEX_PRO': 'PLN_31ksupido3h8d0b',
    'FLEX_UNLIMITED': 'PLN_28x17xi3up6miwc'
}

print("🔄 Syncing Plan Codes...")

for name, code in UPDATES.items():
    try:
        plan = Plan.objects.get(name=name)
        plan.paystack_plan_code = code
        plan.save()
        print(f"✅ Updated {name} -> {code}")
    except Plan.DoesNotExist:
        print(f"❌ Could not find plan '{name}' in database. Please check spelling.")

print("Sync Complete.")
