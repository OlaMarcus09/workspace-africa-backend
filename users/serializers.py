from django.contrib.auth import get_user_model
from rest_framework import serializers
from spaces.models import CheckIn, Subscription # <-- Import the model
from django.utils import timezone

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2')
        extra_kwargs = {'username': {'required': True}}

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

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the /api/users/me/ endpoint.
    Shows the user's details and their subscription status.
    """
    # --- THIS IS THE FIX ---
    # We change this from a direct import to a SerializerMethodField
    # This breaks the circular import loop.
    subscription = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    
    # We need to see the IDs for team and space
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    managed_space = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'username', 
            'photo_url', 
            'user_type',
            'team',
            'managed_space',
            'subscription', # <-- This now uses the method below
            'days_used', 
            'total_days'
        )
    
    def get_subscription(self, obj):
        # We import the serializer *inside* the method
        from spaces.serializers import SubscriptionSerializer 
        # We get the user's *first active* subscription
        sub = obj.subscriptions.filter(is_active=True).first()
        if sub:
            return SubscriptionSerializer(sub).data
        return None

    def get_days_used(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub or not sub.start_date:
             return 0
        
        # We'll calculate days used since the cycle started (more robust logic later)
        days_used = CheckIn.objects.filter(
            user=obj, 
            timestamp__gte=sub.start_date
        ).values('timestamp__date').distinct().count() # Count distinct days
        return days_used

    def get_total_days(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub:
            return 0
        return sub.plan.included_days

class TeamMemberSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing team members.
    (This is what spaces/serializers.py imports)
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url')
