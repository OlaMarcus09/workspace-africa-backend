from rest_framework import serializers
from .models import Plan, PartnerSpace, Subscription, CheckIn, CheckInToken
# We NO LONGER import from users.serializers at the top

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'price_ngn', 'included_days', 'access_tier', 'paystack_plan_code')

class PartnerSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerSpace
        fields = ('id', 'name', 'address', 'amenities', 'latitude', 'longitude', 'access_tier')

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ('id', 'plan', 'start_date', 'end_date', 'is_active')

class CheckInTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckInToken
        fields = ('code', 'expires_at')

class CheckInValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    space_id = serializers.IntegerField()

class SubscriptionCreateSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    paystack_reference = serializers.CharField(max_length=100)
    def validate_plan_id(self, value):
        if not Plan.objects.filter(id=value).exists():
            raise serializers.ValidationError("This plan does not exist.")
        return value
    def validate_paystack_reference(self, value):
        if Subscription.objects.filter(paystack_reference=value).exists():
            raise serializers.ValidationError("This payment has already been processed.")
        return value

# --- THIS IS THE FIX ---
class CheckInReportSerializer(serializers.ModelSerializer):
    """
    Serializer for the Partner's report.
    This no longer imports TeamMemberSerializer, breaking the loop.
    """
    user = serializers.StringRelatedField(read_only=True) 

    class Meta:
        model = CheckIn
        fields = ('id', 'user', 'timestamp')
