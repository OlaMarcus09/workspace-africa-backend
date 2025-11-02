from django.contrib.auth import get_user_model
from rest_framework import serializers
# We need to import our SubscriptionSerializer from the OTHER app
from spaces.serializers import SubscriptionSerializer
from spaces.models import CheckIn # Import CheckIn model
from django.utils import timezone

User = get_user_model() # Gets our CustomUser model

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2')
        extra_kwargs = {
            'username': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        validated_data.pop('password2', None)
        return user

# --- NEW SERIALIZER ---
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the /api/users/me/ endpoint.
    Shows the user's details and their subscription status.
    """
    subscription = SubscriptionSerializer(read_only=True)
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'username', 
            'photo_url', 
            'subscription', 
            'days_used', 
            'total_days'
        )

    def get_days_used(self, obj):
        """
        Calculates the number of days used in the current billing cycle.
        """
        if not hasattr(obj, 'subscription') or not obj.subscription:
            return 0
        
        # For MVP, we'll assume 'start_date' is the beginning of the
        # current billing cycle.
        sub = obj.subscription
        if not sub.start_date:
             return 0
        
        # Count check-ins since the cycle started
        # We'll need to make this logic more robust for monthly renewals later
        days_used = CheckIn.objects.filter(
            user=obj, 
            timestamp__gte=sub.start_date
        ).count()
        return days_used

    def get_total_days(self, obj):
        """
        Gets the total days included in the user's plan.
        """
        if not hasattr(obj, 'subscription') or not obj.subscription:
            return 0
        
        return obj.subscription.plan.included_days
