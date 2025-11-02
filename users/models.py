from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    class UserType(models.TextChoices):
        SUBSCRIBER = 'SUBSCRIBER', 'Subscriber'
        PARTNER = 'PARTNER', 'Partner'
        TEAM_ADMIN = 'TEAM_ADMIN', 'Team Admin' # <-- NEW TYPE
        TEAM_MEMBER = 'TEAM_MEMBER', 'Team Member' # <-- NEW TYPE

    email = models.EmailField(unique=True)
    photo_url = models.URLField(max_length=512, blank=True, null=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.SUBSCRIBER
    )
    managed_space = models.ForeignKey(
        'spaces.PartnerSpace',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers'
    )
    
    # --- NEW FIELD ---
    # If the user is a TEAM_MEMBER, this links them to their team
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
