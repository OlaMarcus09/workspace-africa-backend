from django.contrib.auth import get_user_model
from rest_framework import serializers
from spaces.serializers import SubscriptionSerializer
from spaces.models import CheckIn
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
    subscription = SubscriptionSerializer(read_only=True)
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url', 'subscription', 'days_used', 'total_days')

    def get_days_used(self, obj):
        if not hasattr(obj, 'subscriptions') or not obj.subscriptions.first():
            return 0
        
        sub = obj.subscriptions.first()
        if not sub or not sub.start_date:
             return 0
        
        days_used = CheckIn.objects.filter(user=obj, timestamp__gte=sub.start_date).count()
        return days_used

    def get_total_days(self, obj):
        if not hasattr(obj, 'subscriptions') or not obj.subscriptions.first():
            return 0
        return obj.subscriptions.first().plan.included_days

# --- NEW SERIALIZER ---
class TeamMemberSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing team members.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url')
