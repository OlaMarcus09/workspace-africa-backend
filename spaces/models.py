from django.db import models
from django.conf import settings
import random
from django.utils import timezone

class Plan(models.Model):
    class AccessTier(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard Spaces'
        PREMIUM = 'PREMIUM', 'All Spaces (Standard + Premium)'
    
    name = models.CharField(max_length=100, unique=True)
    price_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    included_days = models.PositiveIntegerField(help_text="Number of days included per month. Use 999 for unlimited.")
    access_tier = models.CharField(max_length=20, choices=AccessTier.choices, default=AccessTier.STANDARD)
    paystack_plan_code = models.CharField(max_length=100, blank=True, null=True, help_text="ID from Paystack for this plan")

    def __str__(self):
        return f"{self.name} - ₦{self.price_ngn}/mo"

class PartnerSpace(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    amenities = models.TextField(blank=True, help_text="Comma-separated list of amenities")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    access_tier = models.CharField(max_length=20, choices=Plan.AccessTier.choices, default=Plan.AccessTier.STANDARD)
    payout_per_checkin_ngn = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=1500.00,
        help_text="Amount (NGN) paid to partner per check-in"
    )

    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='subscriptions',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    plan = models.ForeignKey(Plan, related_name='subscriptions', on_delete=models.PROTECT)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True, help_text="When the subscription expires")
    is_active = models.BooleanField(default=True)
    
    # --- NEW FIELD ---
    paystack_reference = models.CharField(max_length=100, blank=True, null=True, unique=True)

    def __str__(self):
        if self.user:
            return f"{self.user.email} on {self.plan.name}"
        elif hasattr(self, 'team'):
            return f"{self.team.name} on {self.plan.name}"
        return f"Orphaned Subscription on {self.plan.name}"

class CheckIn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='check_ins', on_delete=models.CASCADE)
    space = models.ForeignKey(PartnerSpace, related_name='check_ins', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} checked into {self.space.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class CheckInToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(random.randint(100000, 999999))
            while CheckInToken.objects.filter(code=self.code).exists():
                self.code = str(random.randint(100000, 999999))
        
        if not self.id: 
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Code {self.code} for {self.user.email}"
