import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Finds a user by email and forcefully sets their password.'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')

        if not email or not password or not username:
            self.stdout.write(self.style.ERROR('Superuser ENV VARS are not set. Cannot proceed.'))
            return

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Password for {email} has been forcefully reset.'))
        
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'User {email} not found. Creating new superuser...'))
            try:
                User.objects.create_superuser(
                    email=email,
                    username=username,
                    password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
