from django.db import models
from django.conf import settings
import uuid

class Team(models.Model):
    """
    Represents an SME (company) that buys a team plan.
    """
    name = models.CharField(max_length=255)
    # The admin (SME owner) who manages billing
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='administered_teams',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    # A Team has one subscription
    subscription = models.OneToOneField(
        'spaces.Subscription',
        related_name='team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

class Invitation(models.Model):
    """
    A model to track invitations sent to new team members.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        EXPIRED = 'EXPIRED', 'Expired' # <-- THIS IS THE FIX

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ('team', 'email') # A user can only be invited to a team once

    def __str__(self):
        return f"Invite for {self.email} to join {self.team.name}"
