from rest_framework import serializers
from .models import Plan, PartnerSpace, Subscription, CheckInToken

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'price_ngn', 'included_days', 'access_tier', 'paystack_plan_code')

class PartnerSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerSpace
        fields = (
            'id', 
            'name', 
            'address', 
            'amenities', 
            'latitude', 
            'longitude', 
            'access_tier'
        )

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ('plan', 'start_date', 'end_date', 'is_active')

class CheckInTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckInToken
        fields = ('code', 'expires_at')

# --- NEW SERIALIZER ---
class CheckInValidationSerializer(serializers.Serializer):
    """
    Serializer for the partner to send us a code and their space ID.
    """
    code = serializers.CharField(max_length=6)
    space_id = serializers.IntegerField()
