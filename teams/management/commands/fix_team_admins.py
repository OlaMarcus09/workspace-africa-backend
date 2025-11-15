from django.core.management.base import BaseCommand
from users.models import CustomUser
from teams.models import Team

class Command(BaseCommand):
    help = 'Create teams for Team Admin users without teams'

    def handle(self, *args, **options):
        team_admins = CustomUser.objects.filter(user_type='TEAM_ADMIN')
        
        self.stdout.write(f"Found {team_admins.count()} Team Admin users")
        
        created_count = 0
        for admin in team_admins:
            if not admin.administered_teams.exists():
                team = Team.objects.create(
                    name=f"{admin.username}'s Team",
                    admin=admin
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created team "{team.name}" for {admin.email}')
                )
                created_count += 1
            else:
                team = admin.administered_teams.first()
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {admin.email} already has team: "{team.name}"')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Created teams for {created_count} Team Admin users')
        )
