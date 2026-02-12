from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from spaces.models import CheckIn, Subscription
from django.utils import timezone

User = get_user_model()

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    def validate(self, attrs):
        email = attrs.get('email')
        if not email:
            raise serializers.ValidationError({"email": "Email field is required."})
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found with this email address."})
        if not user.is_active:
            raise serializers.ValidationError({"email": "This account is inactive."})
        attrs['username'] = user.username
        data = super().validate(attrs)
        data['user_id'] = user.id
        data['email'] = user.email
        data['username'] = user.username
        data['user_type'] = user.user_type
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['user_type'] = user.user_type
        return token

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm password')
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2')
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
        return user

class UserProfileSerializerDetailed(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    total_checkins = serializers.SerializerMethodField() # FIX: Added to resolve "0 LIFETIME" logins

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'photo_url', 'user_type',
            'team', 'managed_space', 'subscription', 'plan_name', 
            'days_used', 'total_days', 'total_checkins'
        )
    
    def get_subscription(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if sub:
            from spaces.serializers import SubscriptionSerializer
            return SubscriptionSerializer(sub).data
        return None

    def get_plan_name(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        return sub.plan.name if sub else "FREE_TIER"

    def get_total_checkins(self, obj):
        # FIX: Returns the total count of all check-in records for the user
        return obj.check_ins.count()

    def get_days_used(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub or not sub.start_date:
            return 0
        return CheckIn.objects.filter(
            user=obj, 
            timestamp__gte=sub.start_date
        ).values('timestamp__date').distinct().count()

    def get_total_days(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        if not sub:
            return 0
        
        # --- LOGIC UPDATED ---
        # Since FLEX_UNLIMITED is set to 30 in the database,
        # we return 999 to signal "Unlimited" to the frontend components.
        days = sub.plan.included_days
        return 999 if days >= 30 else days

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url')