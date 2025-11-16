from django.core.management.base import BaseCommand
from spaces.models import PartnerSpace, Plan

class Command(BaseCommand):
    help = 'Add sample coworking spaces to the database'

    def handle(self, *args, **options):
        spaces_data = [
            {
                'name': "Seb's Hub Co-Working Space",
                'address': "No 32, Awolowo Avenue, Bodija, Ibadan, Oyo State, Nigeria",
                'amenities': "AC, Kitchen, Meeting Rooms, Power Backup, Private Offices, Wi-Fi",
                'access_tier': Plan.AccessTier.PREMIUM
            },
            {
                'name': "Worknub Co-working Space",
                'address': "West One Building, beside the office of the governor's wife, Agodi GRA, Ibadan",
                'amenities': "AC, Kitchen, Meeting Rooms, Power Backup, Private Offices, Wi-Fi",
                'access_tier': Plan.AccessTier.PREMIUM
            },
            {
                'name': "Stargate Workstation",
                'address': "Cocoa House, Dugbe, Ibadan, Oyo State, Nigeria",
                'amenities': "AC, Private Offices, Wi-Fi",
                'access_tier': Plan.AccessTier.STANDARD
            },
            {
                'name': "theBUNKer Services Nigeria Limited",
                'address': "Ibadan, Oyo State, Nigeria",
                'amenities': "AC, Kitchen, Meeting Rooms, Power Backup, Private Offices, Wi-Fi",
                'access_tier': Plan.AccessTier.PREMIUM
            },
            {
                'name': "Nesta Co-work Space, Akobo",
                'address': "House 10, Road 17, Bashorun Estate, Akobo, Ibadan",
                'amenities': "Kitchen, Meeting Rooms, Power Backup, Private Offices, Wi-Fi",
                'access_tier': Plan.AccessTier.STANDARD
            },
            {
                'name': "Cyberhaven",
                'address': "Okunmade street, opposite veterinary junction, Ibadan",
                'amenities': "AC, Meeting Rooms, Wi-Fi",
                'access_tier': Plan.AccessTier.STANDARD
            },
            {
                'name': "Atelier Coworking Space & French Café",
                'address': "Ibadan, Oyo State, Nigeria",
                'amenities': "AC, Kitchen, Meeting Rooms, Power Backup, Private Offices, Wi-Fi, Café",
                'access_tier': Plan.AccessTier.PREMIUM
            }
        ]

        created_count = 0
        for space_data in spaces_data:
            space, created = PartnerSpace.objects.get_or_create(
                name=space_data['name'],
                defaults={
                    'address': space_data['address'],
                    'amenities': space_data['amenities'],
                    'access_tier': space_data['access_tier']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created: {space.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Already exists: {space.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new spaces')
        )
