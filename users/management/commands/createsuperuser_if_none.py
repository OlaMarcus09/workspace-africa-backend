import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser if one does not exist.'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')

        if not email or not password or not username:
            self.stdout.write(self.style.WARNING('Superuser env vars not set, skipping creation.'))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser with email {email} already exists.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Creating superuser {email}...'))
            try:
                User.objects.create_superuser(
                    email=email,
                    username=username,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))

