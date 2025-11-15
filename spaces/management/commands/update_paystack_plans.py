from django.core.management.base import BaseCommand
from spaces.models import Plan

class Command(BaseCommand):
    help = 'Update plans with Paystack plan codes'

    def handle(self, *args, **options):
        plans_data = [
            {
                'name': 'Flex Basic',
                'paystack_plan_code': 'PLN_mu2w42h302kwhs4'
            },
            {
                'name': 'Flex Pro', 
                'paystack_plan_code': 'PLN_rlctlj6pkky8t94'
            },
            {
                'name': 'Flex Unlimited',
                'paystack_plan_code': 'PLN_bn2p2x82io1fooy'
            }
        ]

        for plan_data in plans_data:
            try:
                plan = Plan.objects.get(name=plan_data['name'])
                plan.paystack_plan_code = plan_data['paystack_plan_code']
                plan.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated {plan.name} with Paystack code: {plan.paystack_plan_code}')
                )
            except Plan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Plan "{plan_data["name"]}" not found')
                )

        self.stdout.write(
            self.style.SUCCESS('🎉 All plans updated with Paystack codes!')
        )
