from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from spaces.models import PartnerSpace

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_partner_space(sender, instance, created, **kwargs):
    """
    Automate New Partners: Auto-create a Space when a new Partner signs up.
    Triggers on User model save.
    """
    if created and instance.user_type == 'PARTNER':
        PartnerSpace.objects.create(
            owner=instance,
            name=f"{instance.username}'s Space",
            address="Please update your address in Settings",
            city="Ibadan", 
            access_tier="STANDARD",
            is_active=True
        )
