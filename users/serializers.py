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
        extra_kwargs = {'username': {'required': True}}
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
            
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        validated_data.pop('password2', None)
        return user

# SIMPLE UserProfileSerializer without subscription logic
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url', 'user_type', 'team', 'managed_space')

# Keep the detailed one but fix the subscription method
class UserProfileSerializerDetailed(serializers.ModelSerializer):
    subscription = serializers.SerializerMethodField()
    days_used = serializers.SerializerMethodField()
    total_days = serializers.SerializerMethodField()
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    managed_space = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'photo_url', 'user_type',
            'team', 'managed_space', 'subscription', 'days_used', 'total_days'
        )
    
    def get_subscription(self, obj):
        try:
            # Safe import and safe access
            if hasattr(obj, 'subscriptions'):
                sub = obj.subscriptions.filter(is_active=True).first()
                if sub:
                    # Import here to avoid circular imports
                    from spaces.serializers import SubscriptionSerializer
                    return SubscriptionSerializer(sub).data
            return None
        except Exception as e:
            print(f"Subscription error: {e}")
            return None

    def get_days_used(self, obj):
        try:
            if hasattr(obj, 'subscriptions'):
                sub = obj.subscriptions.filter(is_active=True).first()
                if not sub or not sub.start_date:
                    return 0
                days_used = CheckIn.objects.filter(
                    user=obj, 
                    timestamp__gte=sub.start_date
                ).values('timestamp__date').distinct().count() 
                return days_used
            return 0
        except Exception as e:
            print(f"Days used error: {e}")
            return 0

    def get_total_days(self, obj):
        try:
            if hasattr(obj, 'subscriptions'):
                sub = obj.subscriptions.filter(is_active=True).first()
                if not sub:
                    return 0
                return sub.plan.included_days if hasattr(sub, 'plan') else 0
            return 0
        except Exception as e:
            print(f"Total days error: {e}")
            return 0

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'photo_url')
