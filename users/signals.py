from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from spaces.models import PartnerSpace

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_partner_space(sender, instance, created, **kwargs):
    """
    Automate New Partners: Auto-create a Space when a new Partner signs up,
    and link it to the user's managed_space field without signal recursion.
    """
    if created and instance.user_type == 'PARTNER' and not instance.managed_space_id:
        # Check if they already own a space to prevent double creation during seeding
        space = PartnerSpace.objects.filter(owner=instance).first()
        
        if not space:
            space = PartnerSpace.objects.create(
                owner=instance,
                name=f"{instance.username}'s Space",
                address="Please update your address in Settings",
                access_tier="STANDARD",
                is_active=True
            )
        
        # FIXED: Update the user's managed_space directly via queryset
        # This prevents the signal from re-firing recursively!
        sender.objects.filter(pk=instance.pk).update(managed_space=space)
